import pandas as pd
import io

atelerix_table_markdown = """
| Land-Cover Type                     | Habitat Suitability for *A. algirus* | Notes                                                                            |
| ----------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------- |
| Discontinuous Urban Fabric          | Moderate                             | Gardens and green areas may be used; risks from traffic and pets are high        |
| Continuous Urban Fabric             | Low                                  | Highly disturbed, limited food and cover                                         |
| Industrial or Commercial Units      | Very Low                             | Unsuitable due to disturbance and lack of resources                              |
| Airports                            | Very Low                             | Highly disturbed, dangerous, no foraging potential                               |
| Port Areas                          | Very Low                             | Artificial, unsuitable habitat                                                   |
| Sport and Leisure Facilities        | Very Low                             | Artificial surfaces, low ecological value                                        |
| Pastures                            | High                                 | Good for foraging, especially with hedgerows or shrubs                           |
| Non-irrigated Arable Land           | High                                 | Suitable if managed traditionally, field margins important                       |
| Permanently Irrigated Land          | Low                                  | Intensive management, disturbance, chemicals reduce suitability                  |
| Complex Cultivation Patterns        | High                                 | Heterogeneous mosaics provide cover and prey                                     |
| Agriculture with Natural Vegetation | High                                 | High structural diversity supports foraging and shelter                          |
| Sclerophyllous Vegetation           | High                                 | Suitable for cover and prey availability                                         |
| Transitional Woodland-Shrub         | High                                 | Ecotonal habitats favored by hedgehogs                                           |
| Natural Grasslands                  | Moderate-High                        | Good for foraging; less shelter than shrub-dominated habitats                    |
| Broad-leaved Forests                | Moderate                             | Used mainly at edges; closed canopy less suitable                                |
| Mixed Forests                       | Moderate                             | Some suitability at ecotones; dense stands avoided                               |
| Coniferous Forests                  | Low                                  | Limited undergrowth and prey availability                                        |
| Peatbogs                            | Very Low                             | Unsuitable due to saturated soils                                                |
| Inland Marshes                      | Very Low                             | Flooded environments unsuitable                                                  |
| Coastal Lagoons                     | Very Low                             | Unsuitable wetland habitat                                                       |
| Estuaries                           | Very Low                             | Unsuitable wetland habitat                                                       |
| Intertidal Flats                    | Very Low                             | Unsuitable wetland habitat                                                       |
| Water Courses                       | Low-Moderate                         | Depends on adjacent riparian vegetation                                          |
"""

martes_table_markdown = """
| Land-Cover Type                     | Habitat Suitability for *M. martes* | Notes                                                                                 |
| ----------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------- |
| Discontinuous Urban Fabric          | Low                                 | Occasionally traversed; risk from disturbance and traffic; not suitable for residence |
| Continuous Urban Fabric             | Very Low                            | Highly disturbed, no structural refuge                                                |
| Industrial or Commercial Units      | Very Low                            | Unsuitable due to disturbance and absence of prey/cover                               |
| Airports                            | Very Low                            | Highly disturbed, dangerous, no ecological value                                      |
| Port Areas                          | Very Low                            | Artificial environments, unsuitable                                                   |
| Sport and Leisure Facilities        | Very Low                            | Open, artificial surfaces; minimal resources                                          |
| Pastures                            | Low                                 | Limited cover; may be crossed but rarely used                                         |
| Non-irrigated Arable Land           | Low                                 | Low structural diversity; occasional movement corridors                               |
| Permanently Irrigated Land          | Very Low                            | Intensively managed, disturbed, and unsuitable                                        |
| Complex Cultivation Patterns        | Moderate                            | Mosaic with hedgerows and shrubs offers some cover and prey                           |
| Agriculture with Natural Vegetation | Moderate-High                       | Heterogeneous; provides supplementary habitat and corridors                           |
| Sclerophyllous Vegetation           | High                                | Important refuge habitat on Menorca; good structural complexity                       |
| Transitional Woodland-Shrub         | High                                | Valuable ecotonal habitat; good cover and prey availability                           |
| Natural Grasslands                  | Low-Moderate                        | Foraging possible but limited denning opportunities                                   |
| Broad-leaved Forests                | High                                | Preferred continental habitat; suitable on Menorca where present                      |
| Mixed Forests                       | High                                | Suitable due to structural complexity and prey availability                           |
| Coniferous Forests                  | Moderate-High                       | Used extensively in Menorca; especially pine stands                                   |
| Peatbogs                            | Very Low                            | Unsuitable; saturated and open                                                        |
| Inland Marshes                      | Very Low                            | Unsuitable; waterlogged, little cover                                                 |
| Coastal Lagoons                     | Very Low                            | Unsuitable aquatic environment                                                        |
| Estuaries                           | Very Low                            | Unsuitable aquatic environment                                                        |
| Intertidal Flats                    | Very Low                            | Unsuitable aquatic environment                                                        |
| Water Courses                       | Low-Moderate                        | Unsuitable in-stream; potential value if riparian vegetation provides cover           |
"""

eliomys_table_markdown = """
| Land-Cover Type                     | Suitability for *E. quercinus* | Notes                                                                 |
| ----------------------------------- | ------------------------------ | --------------------------------------------------------------------- |
| Discontinuous Urban Fabric          | Low                            | Occasional use of gardens or orchards, but high risks and disturbance |
| Continuous Urban Fabric             | Very Low                       | Unsuitable: no cover, high disturbance                                |
| Industrial or Commercial Units      | Very Low                       | Artificial environments lacking food and shelter                      |
| Airports                            | Very Low                       | High disturbance, open areas                                          |
| Port Areas                          | Very Low                       | Artificial, unsuitable for nesting or foraging                        |
| Sport and Leisure Facilities        | Very Low                       | Artificial surfaces; limited vegetation                               |
| Pastures                            | Low                            | Too open; may be crossed but not inhabited                            |
| Non-irrigated Arable Land           | Low                            | Low structural diversity; occasional use of field margins             |
| Permanently Irrigated Land          | Very Low                       | Intensively managed; little value                                     |
| Complex Cultivation Patterns        | Moderate                       | Heterogeneous mosaics with hedgerows/orchards provide cover and food  |
| Agriculture with Natural Vegetation | Moderate-High                  | Semi-natural patches enhance suitability                              |
| Sclerophyllous Vegetation           | High                           | Mediterranean scrub offers cover and fruit/invertebrates              |
| Transitional Woodland-Shrub         | High                           | Ecotonal habitat with good cover and food resources                   |
| Natural Grasslands                  | Low                            | Too open; little nesting or shelter                                   |
| Broad-leaved Forests                | High                           | Preferred woodland habitat; good arboreal structure                   |
| Mixed Forests                       | High                           | Excellent habitat; structural diversity supports nesting and feeding  |
| Coniferous Forests                  | Moderate-High                  | Suitable where understorey and food resources are present             |
| Peatbogs                            | Very Low                       | Unsuitable; waterlogged and open                                      |
| Inland Marshes                      | Very Low                       | Unsuitable; waterlogged                                               |
| Coastal Lagoons                     | Very Low                       | Unsuitable aquatic habitat                                            |
| Estuaries                           | Very Low                       | Unsuitable aquatic habitat                                            |
| Intertidal Flats                    | Very Low                       | Unsuitable aquatic habitat                                            |
| Water Courses                       | Low-Moderate                   | Limited value; may serve as corridors if vegetated margins exist      |
"""

oryctolagus_table_markdown = """
| Land-Cover Type                     | Suitability for *O. cuniculus* | Notes                                                        |
| ----------------------------------- | ------------------------------ | ------------------------------------------------------------ |
| Discontinuous Urban Fabric          | Low                            | May forage in gardens or open plots, but high disturbance    |
| Continuous Urban Fabric             | Very Low                       | Unsuitable due to density and lack of vegetation             |
| Industrial or Commercial Units      | Very Low                       | Highly artificial; unsuitable                                |
| Airports                            | Very Low                       | Disturbance and absence of habitat                           |
| Port Areas                          | Very Low                       | Artificial, no burrowable soils                              |
| Sport and Leisure Facilities        | Very Low                       | Open and disturbed; no refuge                                |
| Pastures                            | High                           | Optimal open habitat when near cover                         |
| Non-irrigated Arable Land           | High                           | Good forage; especially valuable with field margins          |
| Permanently Irrigated Land          | Low                            | Intensive management and unsuitable crop structures          |
| Complex Cultivation Patterns        | High                           | Heterogeneous mosaics provide both food and cover            |
| Agriculture with Natural Vegetation | High                           | Semi-natural patches create excellent foraging and refuge    |
| Sclerophyllous Vegetation           | High                           | Provides shelter; often adjacent to grasslands               |
| Transitional Woodland-Shrub         | High                           | Favored ecotone habitat with both refuge and nearby forage   |
| Natural Grasslands                  | High                           | Good forage base, especially near shrubs or rocky cover      |
| Broad-leaved Forests                | Moderate                       | Used along edges and clearings, but not in dense interior    |
| Mixed Forests                       | Moderate                       | As above; edges and openings may be occupied                 |
| Coniferous Forests                  | Low-Moderate                   | Used if mosaic with open areas; interior unsuitable          |
| Peatbogs                            | Very Low                       | Unsuitable; saturated soils                                  |
| Inland Marshes                      | Very Low                       | Unsuitable; saturated soils                                  |
| Coastal Lagoons                     | Very Low                       | Unsuitable; saline and aquatic                               |
| Estuaries                           | Very Low                       | Unsuitable; aquatic environment                              |
| Intertidal Flats                    | Very Low                       | Unsuitable; no vegetation or burrowable soil                 |
| Water Courses                       | Low                            | Generally unsuitable; dry riparian margins occasionally used |
"""

suitability_score_dict = {
    'very high': 1,
    'high': 0.9,
    'moderate-high': 0.7,
    'moderate': 0.45,
    'low-moderate': 0.15,
    'low': 0.05,
    'very low': 0
}

suitability_color_map = {
    "very high": "#66ff66",
    "high": "#aaff66",
    "moderate-high": "#ffff66",
    "moderate": "#ffaa66",
    "low-moderate": "#ffaaaa",
    "low": "#ffaaff",
    "very low": "#aaaaff"
}

def generate_suitability_data():

    suitability_dict = {
        'adaptation_atelerix': extract_markdown_table(atelerix_table_markdown),
        'adaptation_martes': extract_markdown_table(martes_table_markdown),
        'adaptation_eliomys': extract_markdown_table(eliomys_table_markdown),
        'adaptation_oryctolagus': extract_markdown_table(oryctolagus_table_markdown)
    }
    return suitability_dict


def extract_markdown_table(text):
    # Remove the separator line for proper parsing
    lines = text.strip().split('\n')
    header = lines[0]
    data_lines = lines[2:] # Skip the header and the separator line

    # Reconstruct the string without the separator line
    processed_table_string = '\n'.join([header] + data_lines)

    df = pd.read_csv(io.StringIO(processed_table_string), sep='|', engine='python')

    # Clean up the DataFrame: remove extra spaces and the first/last empty columns due to the '|' separator
    df = df.dropna(axis=1, how='all')
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Standardize column names
    if len(df.columns) == 3:
        df.columns = ['land_cover_type', 'suitability', 'notes']

    return df