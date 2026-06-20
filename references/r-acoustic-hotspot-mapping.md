# R: Acoustic Call Hotspot Mapping (KDE)

Weighted kernel density estimation (KDE) for visualizing acoustic monitoring call frequency as a continuous hotspot surface in R.

## When to use

- You have passive acoustic recorder locations + call-event counts per recorder
- You want a heatmap that reflects sampling intensity (not just recorder positions)
- Output goes into a manuscript figure (Gate 8.7: Figure and Table Assembly)

## Required R packages

```r
library(readxl)    # Excel input
library(sf)        # spatial vector data
library(ggplot2)   # plotting
library(ggspatial) # scale bar + north arrow
library(MASS)      # kde2d
```

## Core technique: weighted KDE via point repetition

`MASS::kde2d` does not accept weights. Workaround: repeat each recorder point `call_n` times before KDE. A recorder with 82 calls contributes 82 identical points → density is naturally higher.

```r
coords <- st_coordinates(recorder_utm)
rep_idx <- rep(seq_len(nrow(recorder)), times = pmax(recorder$call_n, 1))
coords_w <- coords[rep_idx, ]

kde <- kde2d(coords_w[, "X"], coords_w[, "Y"],
             n = 250, h = c(bandwidth, bandwidth),
             lims = c(xlim, ylim))
```

## Bandwidth selection

Bandwidth `h` controls the spatial smoothness of the hotspot. Rule of thumb:

- **Acoustic monitoring**: ~8 km (gibbon call detection range in forested terrain)
- **Camera trap**: 2–5 km (home-range scale of target species)
- **Point-count transect**: 1–3 km (observer detection radius × 2)

Adjust based on study species' home range and terrain. Document the choice in the figure caption.

## Coordinate cleaning (Chinese Excel data)

Chinese field Excel files often store coordinates with degree/minute symbols:

| Raw value | Cleaned |
|-----------|---------|
| `97.94219893°E` | `97.94219893` |
| `25.14848187°N` | `25.14848187` |
| `97.8597894` | `97.8597894` |

Safe regex: `gsub("[^0-9.]", "", x)` — strips everything except digits and decimal points.

```r
recorder$lon <- as.numeric(gsub("[^0-9.]", "", recorder$`GPS经度`))
recorder$lat <- as.numeric(gsub("[^0-9.]", "", recorder$`GPS纬度`))
```

## Projection: UTM zone selection for SW China

Gaoligong/Yingjiang region (~97.8–98.8°E, ~24.8–25.3°N) falls in **UTM zone 47N** (EPSG:32647). KDE must run in a meter-based CRS, not WGS84 degrees.

```r
utm_crs <- 32647  # WGS 84 / UTM zone 47N
points_utm <- st_transform(points_sf, utm_crs)
```

| Longitude range | UTM zone | EPSG |
|----------------|----------|------|
| 96°–102°E | 47N | 32647 |
| 102°–108°E | 48N | 32648 |
| 108°–114°E | 49N | 32649 |

## Chinese administrative boundaries

Use shapefiles from [DataV GeoAtlas](http://datav.aliyun.com/portal/school/atlas/area_selector) or GADM. Read with `sf::st_read()`:

```r
dehong  <- st_read("德宏傣族景颇族自治州_533100.shp", quiet = TRUE)
baoshan <- st_read("保山市_530500.shp", quiet = TRUE)
```

Both boundary and point data are typically WGS84 (EPSG:4326). Project everything to UTM together before KDE and plotting.

## Full ggplot2 layer assembly order

1. `geom_sf(data = boundaries)` — administrative fill + outline
2. `geom_raster(data = kde_df, aes(fill = z))` — hotspot heatmap (alpha ~0.7–0.8)
3. `scale_fill_gradientn(colors = warm_palette)` — yellow→orange→red→darkred
4. `geom_sf(data = gibbon_utm, shape = 1, color = "red")` — species locations (open circles)
5. `geom_sf(data = recorder_utm, aes(size = call_n), shape = 8)` — recorder locations (stars, size=call count)
6. `annotation_scale()` + `annotation_north_arrow()` — map furniture
7. `theme_minimal()` + custom theme adjustments

## Pitfalls

- **KDE in degrees (EPSG:4326)**: `kde2d` on lon/lat produces distorted density. Always project to UTM first.
- **Zero-weight recorders**: Recorders with 0 calls drop out of KDE if weight=0. Use `pmax(call_n, 1)` so every recorder contributes at least one point.
- **Bandwidth too small**: Produces isolated hotspots at each recorder (no spatial smoothing). Visually misleading — implies precision that doesn't exist for acoustic data.
- **Bandwidth too large**: Washes out all variation. Test 3–5 bandwidth values; choose the one where 2–3 distinct hotspot clusters are visible.
- **Raster z-values near zero**: `scale_fill_gradientn` with `"#ffffff00"` as the first color makes near-zero density transparent, reducing visual clutter.
- **`ggspatial` style**: `north_arrow_fancy_orienteering` works with `which_north = "true"` for UTM maps. Use `north_arrow_minimal` for simpler journals.
- **Heatmap under boundaries**: Place `geom_raster` BEFORE `geom_sf(boundaries)` in the layer stack. Boundaries drawn last will cover KDE spillover outside the study area.

## Complete working example

See the companion template: `templates/r-acoustic-hotspot.R` (a minimal self-contained script).

## Related gates

- Gate 8.7: Figure and Table Assembly — hotspot map is a central figure
- Gate 8.72: Figure-Claim Trace — verify hotspot figure caption matches statistical evidence
- `data-type-routing.md` → Acoustic monitoring section
