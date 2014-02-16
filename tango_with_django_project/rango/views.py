from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from datetime import datetime
from rango.bing_search import run_query

def index(request):
	# Request the context of the request
	# The context contains information such as a client's machine details for example.
	context = RequestContext(request)

	category_list = Category.objects.order_by('-likes')[:5]

	# context_dict = {'categories': category_list}
	context_dict = {'categories': category_list}


	for category in category_list:
		category.url = category.name.replace(' ', '_')

	page_list = Page.objects.order_by('-views')[:5]
	context_dict['pages'] = page_list

	# Construct a dictionary to pass to the template engine as its context.
	# Note the key boldmessage is the same as {{ boldmessage }} in the template!
	# context_dict = {'boldmessage': "I am bold font from the context"}

	# Return a rendered response to send to the client.
	# We make use of the shortcut funtion to make our lives easer.
	# Note that the first parameter is the template we wish to use.


	# return HttpResponse("Rango says hello world!<a href='/rango/about'>About</a>")

	if request.session.get('last_visit'):
		last_visit_time = request.session.get('last_visit')

		visits = request.session.get('visits', 0)

		if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
			request.session['visits'] = visits + 1

	else:
		request.session['last_visit'] = str(datetime.now())
		request.session['visits'] = 1

	return render_to_response('rango/index.html', context_dict, context)

def about(request):
	context = RequestContext(request)

	if request.session['visits']:
		count = request.session['visits']

	else:
		count = 0

	return render_to_response('rango/about.html', {'visit_count': count}, context)
	# return HttpResponse("Rango Says: Here is the about page.<a href='/rango/'>Index</a>")

def category(request, category_name_url):
	# Request our context from the request passed to us.
	context = RequestContext(request)

	# Change underscores in the category name to spaces.
	# URLs don't handle spaces well, so we encode them as underscores.
	# We can then simply replace the underscores with spaces again to get the name.
	category_name = category_name_url.replace('_', ' ')

	# create a context dictionary which we can pass to the template rendering engine.
	# We start by containing the name of the category passed by the user.
	context_dict = {'category_name': category_name, 'category_name_url': category_name_url}

	try:
		# Can we find a category with the given name?
		# If we can't, the .get() method raises a DoesNotExist exception.
		# So the .get() method returns one model instance or raises an exception.
		category = Category.objects.get(name=category_name)

		# Retrieve all of the associated pages.
		# Note that filter returns >= 1 model instance.
		pages = Page.objects.filter(category=category)

		# Adds our results list to the template context under name pages.
		context_dict['pages'] = pages
		# We also add the category object from the database to the context dictionary.
		# We'll use this in the template to verify that the category exists.
		context_dict['category'] = category
	except Category.DoesNotExist:
		# We get here if we didn't find the specified category.
		# Don't do anything - the template displays the "no category" message for us.
		pass

	# Go render the response and return it to the client.
	return render_to_response('rango/category.html', context_dict, context)

def add_category(request):
	# Get the context from the request.
	context = RequestContext(request)

	if request.method == 'POST':
		form = CategoryForm(request.POST)

		if form.is_valid():
			form.save(commit=True)

			return index(request)
		else:
			# print form.errors
			pass
	else:
		form = CategoryForm()

	return render_to_response('rango/add_category.html', {'form': form}, context)

def add_page(request, category_name_url):
	context = RequestContext(request)

	category_name = category_name_url.replace('_', ' ')
	if request.method == 'POST':
		form = PageForm(request.POST)

		if form.is_valid():
			page = form.save(commit=False)

			try:
				cat = Category.objects.get(name=category_name)
				page.category = cat
			except Category.DoesNotExist:

				return render_to_response('rango/add_page.html', {}, context)

			page.views = 0

			page.save()

			return category(request, category_name_url)

		else:
			print form.errors
	else:
		form = PageForm()

	return render_to_response( 'rango/add_page.html',
		{'category_name_url': category_name_url,
		'category_name': category_name, 'form': form},
		context)

def register(request):
	context = RequestContext(request)

	registered = False

	if request.method == 'POST':
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)

		if user_form.is_valid() and profile_form.is_valid():
			user = user_form.save()

			user.set_password(user.password)
			user.save()

			profile = profile_form.save(commit=False)
			profile.user = user

			profile.save()

			registered = True

		else:
			print user_form.errors, profile_form.errors

	else:
		user_form = UserForm()
		profile_form = UserProfileForm()

	return render_to_response(
			'rango/register.html',
			{'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
			context)

def user_login(request):
	context = RequestContext(request)
	context_dict = {}

	if request.method == 'POST':

		username = request.POST['username']
		password = request.POST['password']

		user = authenticate(username=username, password=password)


		if user is not None:

			if user.is_active:

				login(request, user)
				return HttpResponseRedirect('/rango/')
			else:
				context_dict['disabled_account'] = True
				return render_to_response('rango/login.html', context_dict, context)
		else:
			print "Invalid login details: {0}, {1}".format(username, password)
			context_dict['bad_details'] = True
			return render_to_response('rango/login.html', context_dict, context)

	else:
		return render_to_response('rango/login.html', {}, context)

@login_required
def restricted(request):
	context = RequestContext(request)
	return render_to_response('rango/restricted.html', context)

@login_required
def user_logout(request):
	logout(request)

	return HttpResponseRedirect('/rango/')

def search(request):
	context = RequestContext(request)
	result_list = []

	if request.method == 'POST':
		query = request.POST['query'].strip()

		if query:
			# Run our Bing function to get the results list!
			result_list = run_query(query)

	return render_to_response('rango/search.html', {'result_list': result_list}, context)
