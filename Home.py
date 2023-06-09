import pandas as pd
import streamlit as st
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from PIL import Image

# Set page config
st.set_page_config(page_title = 'Home', page_icon = '🏠',layout = "wide")


#============================================
# Functions
#============================================

def clean_code( df ):
   
    '''
        Cleaning dataframe function:
            - Rename columns, clean duplicantes and blank values
            - Create Countries, Continent, average_cost_USD and price_tye columns
            - Remove Outliers
            - Clean the 'cuisines' column
        Input: Dataframe
        Output: Dataframe     
    '''

    #Renaming columns, cleaning duplicates and blank values
    df = df.rename(columns=lambda x: x.lower().replace(' ', '_'))
    df.drop_duplicates(inplace=True)
    df = df.dropna().reset_index()


    #Dictionary to create a column country from country code
    COUNTRIES = {
    1   : "India",
    14  : "Australia",
    30  : "Brazil",
    37  : "Canada",
    94  : "Indonesia",
    148 : "New Zeland",
    162 : "Philippines",
    166 : "Qatar",
    184 : "Singapure",
    189 : "South Africa",
    191 : "Sri Lanka",
    208 : "Turkey",
    214 : "United Arab Emirates",
    215 : "England",
    216 : "USA",
    }

    df['country'] = df['country_code'].map(COUNTRIES)

    #Dictionary to create column of continents from country
    CONTINENT = {
        "India"                : "Asia",
        "Australia"            : "Oceania",
        "Brazil"               : "South America",
        "Canada"               : "North America",
        "Indonesia"            : "Asia",
        "New Zeland"           : "Oceania",
        "Philippines"          : "Asia",
        "Qatar"                : "Asia",
        "Singapure"            : "Asia",
        "South Africa"         : "Africa",
        "Sri Lanka"            : "Asia",
        "Turkey"               : "Asia",
        "United Arab Emirates" : "Asia",
        "England"              : "Europe",
        "USA"                  : "North America"
    }

    df['continent'] = df['country'].map(CONTINENT)

    #Dictionary to convert all currencies to USD
    CONVERT_USD = {
        'Botswana Pula(P)'          : 0.064,
        'Brazilian Real(R$)'        : 0.18,
        'Dollar($)'                 : 1.0,
        'Emirati Diram(AED)'        : 0.27,
        'Indian Rupees(Rs.)'        : 0.013,
        'Indonesian Rupiah(IDR)'    : 0.000070,
        'NewZealand($)'             : 0.69,
        'Pounds(£)'                 : 1.38,
        'Qatari Rial(QR)'           : 0.27,
        'Rand(R)'                   : 0.067,
        'Sri Lankan Rupee(LKR)'     : 0.0051,
        'Turkish Lira(TL)'          : 0.11
    }
        
    df['average_cost_USD'] = df['average_cost_for_two'] * df['currency'].map(CONVERT_USD)

    # Removing outlier
    df = df.drop(index=df[df['average_cost_for_two'] == 25000017].index)

    # Removing values equals do 0 
    df = df[df['aggregate_rating'] != 0]
    df = df[df['average_cost_for_two'] != 0]

    #Classifie price range
    conditions = [df['price_range'] == 1, df['price_range'] == 2, df['price_range'] == 3,df['price_range'] >= 4]
    choices    = ['cheap', 'normal', 'expensive','gourmet']

    # Create a Price Tye from price_range columns
    df['price_tye'] = np.select(conditions, choices, default='valor não encontrado')

    #Simplifing columns cuisines by selecting only the first type of each line
    df["cuisines"] = df.loc[:, "cuisines"].apply(lambda x: x.split(",")[0])

    #Replace 1 and 0 for Yes or No for better appearance in charts
    df[['has_table_booking', 'has_online_delivery']] = df[['has_table_booking', 'has_online_delivery']].replace({0: 'No', 1: 'Yes'})
    
    return df


def consulta_restaurante(df,order):
    '''
        Filtering dataframe to return restaurants cost and rating based on sidebars filters
        Input: Dataframe and order do filter from select_order
        Output: Filtered Dataframe with only Restaurant Name, Average Cost from two and Rating
    '''

    aux = ( df[['restaurant_name','cuisines','average_cost_USD','aggregate_rating']]
                                                       .groupby(['restaurant_name','cuisines'])
                                                       .mean()
                                                       .rename_axis(['Restaurant','Cuisine']) )
    
    aux[['average_cost_USD','aggregate_rating'] ] = aux[['average_cost_USD','aggregate_rating']].round(1)
    aux.columns = ['Average Cost for Two (USD)','Rating']

    if order == 'Top Rated':
        return aux.sort_values(by = 'Rating',ascending = False )
    
    elif order == 'Worst Rated': 
        return aux.sort_values(by = 'Rating',ascending = True )
    
    elif order == 'Most Expensive': 
        return aux.sort_values(by = 'Average Cost for Two (USD)', ascending = False )
    
    elif order == 'Most Affordables': 
        return aux.sort_values(columns = 'Average Cost for Two (USD)',ascending = True )
    

df = pd.read_csv('dataset/zomato.csv')
df = clean_code( df )

#============================================
# SIDEBAR 
#============================================

# Icon
image_path = 'images/zomato.jpg'
zomato_icon = Image.open( image_path )
st.sidebar.image( zomato_icon )


# Sidebar widgets for filtering==============

selected_country = st.sidebar.selectbox('Select country', df['country'].unique() , 1 )

# Storage available options of cities in selected country
city_options = df[df['country'] == selected_country]['city'].unique()
selected_city = st.sidebar.selectbox('Select City', city_options )

# Storage available options of cuisines in selected country and city
cuisine_options   = df[(df['country'] == selected_country) & 
                       (df['city'] == selected_city)]['cuisines'].unique()

selected_cuisines = st.sidebar.multiselect('Select cuisine', cuisine_options, help = 'All options are shown if none is selected')

# If any cuisine is marked on filter, storage list of all options to show on map. Avoiding an error if the user remove all filters
if not selected_cuisines:
    selected_cuisines = cuisine_options

price_tyes_options = df[(df['country'] == selected_country) & 
                        (df['city'] == selected_city) & 
                        (df['cuisines'].isin(selected_cuisines)) ]['price_tye'].unique()

selected_price_tyes = st.sidebar.multiselect('Select price tyes', price_tyes_options , help = 'All options are shown if none is selected')

# If any price tye is marked on filter, storage list of all options to show on map. Avoiding an error if the user remove all filters
if not selected_price_tyes:
    selected_price_tyes = price_tyes_options

select_order = st.sidebar.selectbox('Ordey by', ['Top Rated','Worst Rated','Most Expensive','Most Affordables'])

# Filter the dataframe based on selected filters
filtered_data = df[ (df['cuisines'].isin(selected_cuisines)) & 
                    (df['country'] == selected_country) &
                    (df['city'] == selected_city) &
                    (df['price_tye'].isin(selected_price_tyes)) ]


#============================================
# DASHBOARD
#============================================

st.title("Zomato Restaurants")
st.subheader('Information about the top restaurants in major cities across the Globe!')


with st.container(): #GENERAL INFORMATION
    st.header('General information registered')
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1: 
        st.metric( 'Restaurants ', df['restaurant_id'].nunique() )

    with col2: 
        st.metric( 'Countries', df['country'].nunique() )
    
    with col3: 
        st.metric( 'Cities:', df['city'].nunique() )
    
    with col4: 
        st.metric( 'Votes', '{:,.0f}'.format(df['votes'].sum()) )
    
    with col5: 
        st.metric( 'Cuisines', df['cuisines'].nunique() )

st.markdown("***")
st.markdown('## Map of available restaurants based of filters')

with st.container(): 
    col1,col2 = st.columns(2)

    with col1: #MAP

        # Create a map centered on the mean latitude and longitude of the filtered data
        map_center = [ filtered_data['latitude'].mean(), filtered_data['longitude'].mean() ]
        map = folium.Map(location = map_center, 
                         zoom_start = 12, 
                         tiles = 'CartoDB Positron')

        # Create a marker cluster layer for the map
        marker_cluster = MarkerCluster().add_to(map)

        # Add markers to the marker cluster using apply and lambda
        filtered_data.apply(lambda row: folium.Marker(location = [ row['latitude'], row['longitude'] ],
                                                        popup = row[ ['restaurant_name','cuisines'] ] ,
                                                        use_container_width = True ).add_to(marker_cluster), axis = 1)
        
        # Show the map      
        folium_static(map)
    
    with col2: #FILTERED DATAFRAME
        st.dataframe( consulta_restaurante(filtered_data, select_order) )
