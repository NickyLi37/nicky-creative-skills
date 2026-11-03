# Data

All prep is Python (`example/suzhou/prep/`). Everything ends up in local metres on one frame, so the renderer never touches geographic coordinates.

## Extent and local frame

- Pick the extent from the story, not from the city boundary. Suzhou ran from the Gaoxin district in the west to Caoxieshan and Weiting in the east (32 km), and from Baodai Bridge north past Tiger Hill (21 km), so both "wings" of the modern city and the prologue site fit.
- Use a transverse Mercator projection centred on the story's centre (`prep/common.py`): x east, y north, metres. The board in the renderer has the same extent (`world.js` `EXTENT`), and camera keys are written in these metres.

## Buildings: CMAB

- **Source:** CMAB (Zhang, Zhao & Long), a nationwide building dataset for China with footprint, height and age. License CC BY 4.0. Credit it on the end card and cite the version actually downloaded; the current Figshare version was published in 2025, while the production notes refer to the earlier paper.
- **Fields:** `Height` (m) and `Age` (year). Shapefiles come in EPSG:3857, so reproject before clipping.
- **Height is compressed.** The tallest Suzhou building in CMAB was about 104 m. Supertall towers must be overridden from OSM `height` or official figures, and drawn as separate meshes (Suzhou IFS 450 m, 环球188 282 m, 苏州中心 222 m). Otherwise the film's height chapter falls flat.
- **Age covers about 1985–2018,** with a large "1984 or earlier" bucket. Use it for modern growth only.
- **Packing** (`prep/cmab_buildings.py`): extrude footprints into one indexed mesh. Each vertex stores base/top (0/1), its building's height, and meta = (age year, zone × 1000 + random), so the shader can scale heights and reveal buildings without new geometry. Suzhou packed 92,681 buildings into 2.15 M vertices / 3.03 M triangles, an 88 MB binary that loads in a couple of seconds.

## Water, roads, walls: OpenStreetMap

- Fetch each layer separately from Overpass (`prep/fetch_osm.py`) so one can be re-fetched without the others: water polygons and canals, roads by class, city wall remains, gates, bridges, named heritage sites, tall-building heights.
- `prep/osm_layers.py` converts them to compact local-metre JSON.
- Credit: © OpenStreetMap contributors, ODbL.

## Thematic layers

`prep/film_layers.py` builds everything that is not a dataset as such:

- moat and wall rings
- gate positions (land and water gates)
- bridges
- the 1860 fire corridor along Shantang Street
- gardens
- a "field" raster (`field.bin`, Float32 RGBA): distance through water from the Grand Canal entry for the travelling wave, distance to the moat, the fire corridor parameter, and a water mask

Rasters like this let one shader do flow, glow and burn effects without per-frame CPU work.

## Historical maps

The 1229 Pingjiang stele (平江图) is schematic. A thin-plate spline bends its straight streets into nonsense, so georeference it with a **least-squares affine** through hand-picked control points (`prep/pj_georef.py`). Then measure how much still matches: 44 of 169 traced canals lie within 70 m of today's water. That number becomes a line in the script. The Suzhou tracing used [Siyuwj's photograph of the Pingjiang stele](https://commons.wikimedia.org/wiki/File:%E5%9B%9B%E5%A4%A7%E5%AE%8B%E7%A2%91%E2%80%94%E2%80%94%E5%B9%B3%E6%B1%9F%E5%9B%BE%EF%BC%8C2016-05-15.jpg) (Wikimedia Commons, CC BY-SA 4.0) as a reference; Siyuwj supplied the photograph, not a separate tracing file. Credit the source image and follow its license when making and distributing derived tracing assets.

For the image itself, look for public-domain scans first. The example uses a 1930s rubbing photo from 亜細亜大観 (Commons, public domain); the other photos were BY-SA.

## Satellite underlay

Sentinel-2 cloudless 2016 by EOX (`prep/satellite.py`) is CC BY 4.0 and usable in a film. The 2017 layer returned blank tiles, and 2018 and later are non-commercial. At 10 m resolution it only ever reads soft, so use it as a blend stage between the old map and the model.

## Keep a sources list as you go

Every file in `data/layers/` should trace back to a source and license. Write that list into the plan doc while fetching. Rebuilding it at the end is how credits go wrong.
