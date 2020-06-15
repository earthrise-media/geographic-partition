import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import altair as alt
import numpy as np
import geopandas

from sklearn.cluster import KMeans
from shapely.geometry import Polygon, box, mapping
from shapely.ops import unary_union

st.header("Partitioning fields and calculating carbon footprint")

st.markdown("""

We don't know how people will interact with carbon removal through consumer
applications.  We barely understand the cost to remove carbon through
regenerative agricultural practices; we have almost no clue how to calculate
the social value of a tCO2 removed; and the price for consumers has never been
tested at scale.  Fortunately, testing the consumer price of carbon is
flexible &mdash; there are a lot of degrees of freedom to bundle carbon
removal for sale, since sequestration potential varies continuously through
space and time.

**The objective of this lightweight web app is to identify the size and
implied price of an SKU for the Hudson Carbon marketplace.**

We have decided to partition the landscape using the [what3words
grid](https://what3words.com).  There is no _right_ way to geographically
partition the world, but there is a large developer community around this
particular partition.  As such, there are potentially useful services for
back- and front-end development &mdash; including one-line integrations of the
global grid for mobile applications.

""")

st.sidebar.markdown("""
**Value of carbon removal**

""")


carbon_content = st.sidebar.number_input(
	'Credited sequestration (tCO2/acre/year)',
	0.1, 20.0, step=0.1, value=7.7
)

carbon_price = st.sidebar.number_input(
	'Price of carbon ($/tCO2)',
	5, 200, step=1, value=100
)

price_per_plot = np.round(carbon_price * carbon_content * 9 / 4046, 2)

st.markdown("""

The price per what3words plot is based on the following assumptions:

1. **%s** tCO2 credited per acre, annually [check this]
2. **$%s** per tCO2

You can play with these assumptions in the sidebar.  The implied price for
each 3m x 3m plot is **$%s**.


When all is said and done, we want a static, canonical GeoJSON file to define
the geographic partition for each field, like [**this
one**](https://gist.github.com/danhammer/170f314fd5bdffcda2ff34ee7e400263). 
This file will define the SKUs forever after.

Consider a relatively small field: `BSF 3` on Sirmon Farm. Use the slider
below to define the target number of what3words plots per parcel.  The charts
below show:

1. The total number of parcels available at each price.
2. The geographic partitioning of the field.

Note that the target number is not always matched.  In order to ensure that
all area within a field is captured in the marketplace, some parcels will be
bigger than others.  This is ok.  In fact, it's good design.  It provides
some marginal variability and therefore consumer choice which has proven to be
a successful way to capture consumer surplus and move product. The clusters
are calculated and mapped on the fly, so even for a specific set of
parameters, the results may be different.  This is why we need a canonical
partition, once we figure out the appropriate parameters (e.g., price and
carbon content for each field).  

This toy web app starts up and runs slowly since we are not paying for
servers.

""" % (np.round(carbon_content, 1), int(carbon_price), price_per_plot))


N = st.slider(
	'Target number of plots per parcel',
	5, 200, 10
)



df = pd.read_pickle("bsf3.pkl")
size_parcel = N
geovec = list(zip(df.center_x, df.center_y))
number_parcels = int(len(geovec)/size_parcel)
kmeans = KMeans(n_clusters=number_parcels, random_state=0).fit(geovec)
df["parcel"] = kmeans.labels_
df["geometry"] = df[["w", "s", "e", "n"]].apply(lambda x: box(*x), axis=1)

agg_df = df[["parcel", "geometry"]].groupby('parcel').agg(unary_union).reset_index()

count_df = df[["id", "parcel"]].groupby("parcel").agg("count").reset_index()
count_df["price"] = price_per_plot * count_df.id


c = alt.Chart(count_df).mark_bar().encode(
    x=alt.X(
    	"price:Q", 
    	bin=True,
    	axis=alt.Axis(
    		title="Price per parcel-variant ($)"
    	)
    ),
    y=alt.Y(
    	'count()',
    	axis=alt.Axis(
			title="Number of Parcels"
		)
	)
)

st.altair_chart(c, use_container_width=True)

g = geopandas.GeoDataFrame(agg_df, geometry='geometry')
n_parcels = len(count_df.id)

g.boundary.plot(
	figsize=(8,8)
)
plt.box(False)
plt.axis('off')

st.subheader("Geographic partition of Field `BSF 3`: %s parcels" % n_parcels)

st.pyplot()

st.markdown("""

Note that the Stripe transaction fees may be as high as 30 cents.  We are
talking to the leadership and board of Stripe to make an in-kind contribution
to Hudson Carbon by waiving these fees as part of their carbon removal
program.  However, if that does not work, a minimum number of parcels will
have to be purchased, assuming an extremely small parcel size (e.g., 2 plots
per parcel).

""")

st.subheader("Calculator")

st.markdown("""

I will add notes about a carbon calculator here &mdash; assumptions, calculations, etc.

""")



st.sidebar.markdown("""

-----
**Carbon footprint**

""")

car_mileage = st.sidebar.number_input(
	'How many miles do you travel by car each day?',
	0, 200, step=1, value=40
)


flight_number = st.sidebar.number_input(
	'How many flights do you take each year?',
	0, 50, step=1, value=10
)


meat_consumption = st.sidebar.number_input(
	'How many times each week do you eat meat?',
	0, 20, step=1, value=5
)

household_num = st.sidebar.number_input(
	'How many people in your household?',
	0, 10, step=1, value=4
) 

















