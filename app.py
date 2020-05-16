import pandas as pd
import numpy as np
import networkx as nx
import altair as alt
from altair import datum
import time

import streamlit as st
import json
from vega_datasets import data


import sys

sys.path.insert(0, "/app/.heroku/python/lib/python3.6/site-packages")
sys.path.insert(0, "/app/.heroku/python/lib/python3.6/site-packages/nxmetis")

import nxmetis


st.header("Partitioning geographic space.")

st.markdown("""

The objective of this web visualization is to demonstrate the speed of
partitioning a geographic region into clusters of size **n**.  Each cluster is
composed of smaller geographic units that are adjacent to at least one other
unit in the cluster.  



A few issues with this first attempt:

1. We use an [adjacency matrix from the U.S.
Census](https://www.census.gov/geographies/reference-files/2010/geo/county-adjacency.html)
and I haven't quite figured out how adjacency is defined exactly.  It's not
worth the time to figure that out, since this is a dummy example and we will
use a more regular grid (where adjacency is defined as sharing two vertices). 
It's clear that "adjacent" counties may only touch in a single point, barely.

2. I haven't figured out a good way to visualize the results.  There is
probably a really slick way to use the four-color theorem, but again this is
overkill for this example since we will ultimately just be highlighting one
cluster at a time in the Hudson Carbon front-end.  This issue does, however,
make it difficult to view the results in this web visualization.

3. The algorithm will have a remainder.  Sometimes not all of the counties
will be included in a cluster.  The idea is to limit the number of remaining
counties.

4. This is a work in progress.  There will be some failures with edge cases. 
We will deal with that.  But the objective, again, is just to demonstrate
what's possible.


""")

size = st.slider('Size of cluster.', 2, 10, 5)

state_ids = {
	"Texas":            [48000, 49000],
	"Virginia":         [51000, 52000],
	"Florida":          [12000, 13000],
	"Kansas":           [20000, 21000],
	"Indiana":          [18000, 19000],
	"Georgia":          [13000, 14000],
	"California":       [6000, 7000],
	"Random assortment":[6000, 30000]
}

option = st.selectbox(
	"Select a state or region.",
	list(state_ids.keys())
)


starttime = time.time()


id_start, id_end = state_ids[option]


counties = alt.topo_feature(data.us_10m.url, 'counties')

df = pd.read_csv(
	'county_adjacency.tsv', 
	sep="\t", 
	usecols=["county_zip", "adjacent_county_zip"]
)

adjdata = df[
	(df.county_zip > id_start) & 
	(df.county_zip < id_end) &
	(df.adjacent_county_zip > id_start) & 
	(df.adjacent_county_zip < id_end) 
]



county_ids = adjdata["county_zip"].unique().tolist()
number_of_counties = len(county_ids)

am = pd.DataFrame(np.zeros(shape=(number_of_counties, number_of_counties)))

am.index = county_ids
am.columns = county_ids

# Create edges between county codes as tuples
edges = [
	[int(v[0]), int(v[1])] for k, v in adjdata.iterrows() 
	if v[0] != v[1]
]

for e in edges:
	k, v = e
	am.at[k, v] = 1

graph = nx.from_pandas_adjacency(am)


def create_chart(G, N, size=3, id_start=48000, id_end=49000):
	nparts = int(N / size)
	partition_results = nxmetis.partition(G, nparts=nparts)

	acceptable_parts = [x for x in partition_results[1] if len(x) == size]
	dd = pd.DataFrame(dict(id=county_ids, c=-1)).set_index("id")

	i = 0
	j = 0
	for cluster in acceptable_parts:
		
		for idx in cluster:
			dd.at[idx, "c"] = i
			j += 1

		i += 1

	lookup_table = dd.reset_index()
	lookup_table = lookup_table.astype({'c': int})

	c = alt.Chart(counties).mark_geoshape(
				stroke='grey', strokeWidth=0.5
			).encode(
				color=alt.Color('c:Q', legend=None)
			).transform_lookup(
				lookup='id',
				from_=alt.LookupData(lookup_table, 'id', ['c'])
			).transform_filter(
				(datum.id > id_start) & (datum.id < id_end)
			).project(
				type='albersUsa'
			).properties(
				height=600
			).configure_view(
				strokeWidth=0
		)

	return {
		"chart": c,
		"coverage": j
	}

res = create_chart(
	graph, 
	number_of_counties, 
	size=size, 
	id_start=id_start, 
	id_end=id_end
)

endtime = time.time()


st.markdown("""

Each cluster of size *n* = %s is represented on the following map.  The total
coverage was %s of %s total counties, i.e., %s counties (%s percent) were left out of a
cluster.  The time to read the GeoJSON from a remote table, create an
adjacency matrix, and partition the geographic area was **%s seconds**.

> Note that it may be hard to see the separate clusters given my shitty
visualization.  However, it is true that each cluster is of size *n*.

""" % (
		size,
		res["coverage"], 
		number_of_counties,
		number_of_counties - res["coverage"],
		int(100 * (number_of_counties - res["coverage"]) / number_of_counties),
		np.round(endtime-starttime, 3)
	)
)

st.altair_chart(
	res["chart"],
	use_container_width=True
)
