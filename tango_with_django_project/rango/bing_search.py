import json
import urllib, urllib2

def run_query(search_terms):
	# Specify the base
	root_url = 'https://api.datamarket.azure.com/Bing/Search/'
	source = 'Web'

	# Specify how many results to return per page.
	results_per_page = 10
	offset = 0

	# Wrap quotes around our query terms as required by the Bing API
	query = "'{0}'".format(search_terms)
	query = urllib.quote(query)

	# Construct the latter part of our request's URL
	search_url = "{0}{1}?$format=json&$top={2}&$skip={3}&Query={4}".format(
		root_url,
		source,
		results_per_page,
		offset,
		query)

	# Setup authentication with the Bing servers
	# The username MUST be a blank string, and put in your API key!
	username = ''
	bing_api_key = 'BMFnIEEG3vpTV1UM0MxyhSlY41RdDvDtK+CQbE0dTbA'

	# Create a 'password manager' which handles authentication for us.
	password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
	password_mgr.add_password(None, search_url, username, bing_api_key)

	# Create our results list
	results = []

	try:
		# Prepare of connecting to Bing's servers.
		handler = urllib2.HTTPBasicAuthHandler(password_mgr)
		opener = urllib2.build_opener(handler)
		urllib2.install_opener(opener)

		# Connect to the server and read the response generated.
		response = urllib2.urlopen(search_url).read()

		# Convert the string response to a Python dictionary object
		json_response = json.loads(response)

		# Loop through each page returned, populating out results list.
		for result in json_response['d']['results']:
			results.append({
				'title': result['Title'],
				'link': result['Url'],
				'summary': result['Description']})

	# Catch a URLError exception
	except urllib2.URLError, e:
		print "Error when querying the Bing API: ", e

	# Return the list of results to the calling function.
	return results

def main():
	# Query, get the results and create a variable to store rank.
	query = raw_input("Please enter a query: ")
	results = run_query(query)
	rank = 1

	# Loop through our results.
	for result in results:
		# Print details.
		print "Rank {0}".format(rank)
		print result['title']
		print result['link']
		print

		# Increment our rank counter by 1.
		rank += 1

if __name__ == '__main__':
	main()
