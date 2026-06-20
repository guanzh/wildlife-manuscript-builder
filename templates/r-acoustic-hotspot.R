# Acoustic call hotspot mapping — minimal self-contained template
# Copy this file, replace the data paths, adjust bandwidth, run.
#
# Dependencies: readxl, sf, ggplot2, ggspatial, MASS

library(readxl)
library(sf)
library(ggplot2)
library(ggspatial)
library(MASS)

# ============================================================
# 1. READ DATA — replace paths with your files
# ============================================================
species    <- read_excel("species_locations.xlsx")
recorders  <- read_excel("recorder_locations.xlsx")
calls      <- read_excel("call_records.xlsx")
boundary   <- st_read("admin_boundary.shp", quiet = TRUE)

# ============================================================
# 2. CLEAN COORDINATES
# ============================================================
recorders$lon <- as.numeric(gsub("[^0-9.]", "", recorders$`GPS经度`))
recorders$lat <- as.numeric(gsub("[^0-9.]", "", recorders$`GPS纬度`))
recorders <- recorders[!is.na(recorders$lon) & !is.na(recorders$lat), ]

# ============================================================
# 3. COUNT CALLS PER RECORDER
# ============================================================
call_tab <- table(calls$录音机编号)
recorders$call_n <- as.integer(call_tab[recorders$设备编号])
recorders$call_n[is.na(recorders$call_n)] <- 0

# ============================================================
# 4. CONVERT TO sf + PROJECT
# ============================================================
species_sf   <- st_as_sf(species,   coords = c("经度", "纬度"), crs = 4326)
recorder_sf  <- st_as_sf(recorders, coords = c("lon",  "lat"),  crs = 4326)

utm_crs <- 32647  # UTM 47N — adjust for your longitude
species_utm  <- st_transform(species_sf,  utm_crs)
recorder_utm <- st_transform(recorder_sf, utm_crs)
boundary_utm <- st_transform(boundary,    utm_crs)

# ============================================================
# 5. WEIGHTED KDE (repeat points by call count)
# ============================================================
bandwidth <- 8000  # meters — adjust for your species/terrain

coords <- st_coordinates(recorder_utm)
rep_idx <- rep(seq_len(nrow(recorder_utm)), times = pmax(recorders$call_n, 1))
coords_w <- coords[rep_idx, ]

bbox <- st_bbox(recorder_utm)
kde <- kde2d(
  coords_w[, "X"], coords_w[, "Y"],
  n = 250,
  h = c(bandwidth, bandwidth),
  lims = c(bbox["xmin"] - bandwidth * 2, bbox["xmax"] + bandwidth * 2,
           bbox["ymin"] - bandwidth * 2, bbox["ymax"] + bandwidth * 2)
)

kde_df <- expand.grid(x = kde$x, y = kde$y)
kde_df$z <- as.vector(kde$z)

# ============================================================
# 6. PLOT
# ============================================================
p <- ggplot() +
  # Administrative boundary
  geom_sf(data = boundary_utm, fill = "grey92", color = "grey65", linewidth = 0.3) +

  # Hotspot heatmap
  geom_raster(data = kde_df, aes(x = x, y = y, fill = z), alpha = 0.8) +
  scale_fill_gradientn(
    colors = c("#ffffff00", "#fee090", "#fdae61", "#f46d43", "#d73027", "#a50026"),
    values = c(0, 0.05, 0.2, 0.45, 0.7, 1),
    name = "Call density",
    guide = guide_colorbar(barwidth = 0.8, barheight = 8, title.position = "top")
  ) +

  # Species locations — red open circles
  geom_sf(data = species_utm, shape = 1, color = "red", size = 3, stroke = 1.2) +

  # Recorder locations — stars, sized by call count
  geom_sf(data = recorder_utm, aes(size = call_n), shape = 8,
          color = "#2c7bb6", fill = "#2c7bb6", stroke = 0.5) +
  scale_size_continuous(name = "Call count", range = c(1.5, 10),
                        breaks = c(1, 10, 25, 50, 80)) +

  # Map furniture
  annotation_scale(location = "bl", width_hint = 0.25,
                   style = "ticks", line_width = 0.5, text_cex = 0.8) +
  annotation_north_arrow(location = "tr", which_north = "true",
                         height = unit(1.0, "cm"), width = unit(0.8, "cm"),
                         style = north_arrow_fancy_orienteering) +

  labs(
    title    = "Species locations and call hotspot distribution",
    subtitle = sprintf("KDE bandwidth: %.0f km  |  %d recorders, %d call events",
                       bandwidth / 1000, nrow(recorders), nrow(calls)),
    caption  = sprintf("Coordinate system: WGS 84 / UTM zone %dN",
                       as.integer(sub("^32", "", as.character(utm_crs))))
  ) +

  theme_minimal(base_size = 11) +
  theme(
    plot.title       = element_text(face = "bold", size = 15, color = "grey20"),
    plot.subtitle    = element_text(size = 8.5, color = "grey45", margin = margin(b = 8)),
    plot.caption     = element_text(size = 7, color = "grey60"),
    panel.grid       = element_line(color = "grey90", linewidth = 0.2),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background  = element_rect(fill = "white", color = NA),
    legend.position  = "right",
    axis.title       = element_blank()
  )

# ============================================================
# 7. SAVE
# ============================================================
ggsave("hotspot_map.png", plot = p, width = 13, height = 11, dpi = 300, bg = "white")
message("Saved: hotspot_map.png")
