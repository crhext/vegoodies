import os
from jinja2 import Template
import sys
import csv
from flask import Flask, render_template, url_for, request, redirect, Markup
from werkzeug.utils import secure_filename
import random
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

MYDIR = os.path.dirname(__file__)

app.config["IMAGE_UPLOADS"] = 'static/assets/images'
app.config["ALLOWED_IMAGE_EXSTENSIONS"] = ["PNG", "JPG", "JPEG", "GIF"]
app.config["MAX_IMAGE_FILESIZE"] = 0.5*1024*1024

ENV = 'prod'

if ENV == 'dev':
	app.debug = True
	app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://chrishext:chris123@localhost/vegoodies'
else:
	app.debug = False
	app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://bandmyjijalmrg:bc70e5ce190d68cbf124fb126df635558d86a2aae22088642dd4cffc13e95654@ec2-54-86-170-8.compute-1.amazonaws.com:5432/d181a23h4g080h'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Recipes(db.Model):
	_tablename_ = 'Recipes'
	id = db.Column(db.Integer, primary_key=True)
	recipe_type = db.Column(db.String(30))
	title = db.Column(db.String(100))
	name = db.Column(db.String(100), unique=True)
	overview = db.Column(db.String(5000))
	method = db.Column(db.String(20000))
	ingredients = db.Column(db.String(20000))
	tags = db.Column(db.String(5000))
	portions = db.Column(db.String(200))
	author = db.Column(db.String(100))
	image = db.Column(db.String(100))

	def __init__(self, recipe_type, title, name, overview, method, ingredients, tags, portions, author, image):
		self.recipe_type = recipe_type
		self.title = title
		self.name = name
		self.overview = overview
		self.method = method
		self.ingredients = ingredients
		self.tags = tags
		self.portions = portions
		self.author = author
		self.image = image



def allowed_image(filename):
	if not '.' in filename:
		return False

	ext = filename.rsplit('.',1)[1]
	if ext.upper() in app.config["ALLOWED_IMAGE_EXSTENSIONS"]:
		return True
	else:
		return False


def get_contents_overview(page_name, recipe_count):
	if recipe_count == 0:
		overview = 'Boo, there are no recipes found. Please <a href="./add" title="Add a Recipe"> add a recipe</a>!'
	else:
		if page_name == 'mains':
			overview = 'Click on the links below for recipies and ingredients for your favourite mains'
		elif page_name == 'breakfasts':
			overview = 'Click on the links below for recipies and ingredients for your favourite breakfasts'
		elif page_name == 'desserts':
			overview = 'Click on the links below for recipies and ingredients for your favourite desserts'
		elif page_name == 'lunches':
			overview = 'Click on the links below for recipies and ingredients for your favourite lunches'
		elif page_name == 'snacks':
			overview = 'Click on the links below for recipies and ingredients for your favourite snacks'
		else:
			overview = 'Click on the links below for recipies and ingredients for your favourite vegoodies'
	return overview 

def get_contents_title(page_name):
	if page_name == 'mains':
		title = 'Mains'
	elif page_name == 'breakfasts':
		title = 'Breakfasts'
	elif page_name == 'desserts':
		title = 'Desserts'
	elif page_name == 'lunches':
		title = 'Lunches'
	elif page_name == 'snacks':
		title = 'Snacks & Sides'
	return title 

def create_contents_div(recipe_li, overview):
	tile_div = ''
	for i in recipe_li:
		recipe_type = i['recipe_type']
		recipe_name = i['name']
		recipe_title = i['title']
		overview = i['overview']
		image = i['image']
		div = f'''
		<div class="grid-item">
			<a href="/{recipe_type}/{recipe_name}">
				<img class="img-responsive" alt="" src="./static/assets/images/{image}">
				<h2>{recipe_title}</h2>
			</a>
			<p>{overview}</p>
		</div>
		'''
		tile_div += div
	return tile_div	

def get_contents_recipe_li(page_name):
	recipe_li = []
	database_recipe_li = db.session.query(Recipes).filter(Recipes.recipe_type == page_name).all()
	for row in database_recipe_li:
		recipe_dict = row.__dict__
		recipe_li.append(recipe_dict)

	# print(recipe_li)

	# csv_list = csv.DictReader(open('database.csv'))	
	# recipe_li = []
	# for i in csv_list:
	# 	if i['recipe_type'] == page_name:
	# 		recipe_li.append(i)
	return recipe_li

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/<string:page_name>')
def html_contents_page(page_name):
	recipe_title = get_contents_title(page_name)
	recipe_li = get_contents_recipe_li(page_name)
	overview = get_contents_overview(page_name, len(recipe_li))
	tile_divs = create_contents_div(recipe_li,overview)
	return render_template('contentstemplate.html', recipe_title=recipe_title, overview=overview, tile_divs=tile_divs)

@app.route('/<string:page_name>/<string:recipe_name>')
def html_recipe_page(page_name,recipe_name):
	if db.session.query(Recipes).filter(Recipes.name == recipe_name).count()==0:
		return render_template('notfound.html')
	else:
		recipe = db.session.query(Recipes).filter(Recipes.name == recipe_name)
		for row in recipe.all():
			recipe_dict = row.__dict__
			if 'noimage' in recipe_dict['image']:
				image_name = ''
			else:
				image = recipe_dict['image']
				image_name = f'/static/assets/images/{image}'
			if recipe_dict['author'] == '':
				recipe_author = 'Anonymous'
			else:
				recipe_author = recipe_dict['author']
		return render_template('recipetemplate.html', recipe=recipe_dict, image_name=image_name, recipe_author=recipe_author)


@app.route('/add')
def html_add_recipe():
	return render_template('add.html')

@app.route('/somethingwentwrong')
def something_went_wrong():
	return render_template('somethingwentwrong.html')

@app.route('/submitted/<string:recipe_directory>')
def html_submitted_recipe(recipe_directory):
	recipe_type = recipe_directory.split('_')[0]
	recipe_name = recipe_directory.split('_')[1]
	link = f'/{recipe_type}/{recipe_name}'
	return render_template('submitted.html', link=link)


@app.route('/submit_form', methods=['POST', 'GET'])
def submit_form():
	if request.method == 'POST':
		data = request.form.to_dict()
		recipe_title = data['title']
		recipe_name = data['title'].replace(' ','').lower()
		recipe_type = data['type']
		recipe_overview = data['overview']
		recipe_method = data['method']
		recipe_ingredients = data['ingredients']
		recipe_tags= data['tags']
		recipe_portions= data['portions']
		recipe_author = data['author']

		if request.files:
			image = request.files["image"]
			if not image.filename == '':
				if not allowed_image(image.filename):
					print("file must be an image")
					return redirect(request.url)
				else:
					filename = secure_filename(image.filename)
					image.save(os.path.join(MYDIR + "/" + app.config["IMAGE_UPLOADS"], filename))

		if image.filename == '':
			image_name = f'noimage{random.randrange(1,4)}.jpg'
		else:
			image_name = image.filename

		print(recipe_method)

		if recipe_method == '':
			return render_template('add.html', message="Please enter required fields.")
		else:
			pass

		if db.session.query(Recipes).filter(Recipes.name == recipe_name).count()==0:
			database = Recipes(recipe_type, recipe_title, recipe_name, recipe_overview, recipe_method, recipe_ingredients, recipe_tags, recipe_portions, recipe_author, image_name)
			db.session.add(database)
			db.session.commit()
			return redirect(f'/submitted/{recipe_type}_{recipe_name}')
		else:
			return render_template('add.html', message="This recipe name already exists. Please try again.")
	else:
		return redirect('/somethingwentwrong')















# @app.route('/<string:page_name>/<string:recipe_name>')
# def recipe_name(page_name, recipe_name):
# 	return render_template(f'/{page_name}/{recipe_name}.html')

# 	csv_list = csv.DictReader(open('database.csv'))
# 	print(csv_list)
# #	html = write_to_file(recipe_dict)
# #	return html
# 	print('hello')


	# type = data['type']
	# with open(f'templates/{type}/{doc_name}.html', "w") as file:
	# # 	file.write(result)

	# def write_to_file(data):
	# with open('./templates/recipetemplate.html') as file_:
	# 	template = Template(file_.read())
	# result = template.render(recipe_type=data['recipe_type'],title=data['title'],overview=data['overview'],method=data['method'],ingredients=data['ingredients'],tags=data['tags'], )
	# return result

	# @app.route('/<string:page_name>/<int:page_id>')
# def recipes(page_name, page_id):
# 	return render_template(f'/{page_name}/{page_id}.html')






 	# csv_list = csv.DictReader(open('database.csv'))
 	# li = []
 	# for i in csv_list:
 	# 	if i['name'] == recipe_name:
 	# 		li.append(i)
 	# 		if 'noimage' in i['image']:
 	# 	 		image_name = ''
 	# 		else:
	 # 			image = i['image']
	 # 			image_name = f'/static/assets/images/{image}'

 	# if len(li) >= 1:
 	# 	recipe = li[0]
 	# 	return render_template('recipetemplate.html', recipe=recipe, image_name=image_name)
 	# else:
 	# 	return render_template('notfound.html')


		# with open('database.csv', 'a') as csvfile:
		# 	fieldnames = ['recipe_type', 'title', 'name', 'overview', 'method', 'ingredients', 'tags', 'portions', 'author', 'image']
		# 	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		# 	writer.writerow({'recipe_type': recipe_type, 'title': data['title'], 'name': recipe_name, 'overview':data['overview'], 'method':data['method'], 'ingredients':data['ingredients'],'tags':data['tags'],'portions':data['portions'],'author':data['author'],'image':image_name })

		# return redirect(f'/submitted/{recipe_type}_{recipe_name}')