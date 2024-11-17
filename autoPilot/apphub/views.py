from django.shortcuts import render, redirect
from django.conf import settings
import os
from .forms import GeneratedAppForm, ModelFieldFormSet
from django.http import HttpResponse
from .models import GeneratedApp, ModelField
import logging
from django.core.management import call_command
from django.http import HttpResponse



def index(request):
    return HttpResponse("Welcome to the AppHub!")


# Helper function to create the app directory and necessary files
def create_app_directory(app_name):
    app_path = os.path.join(settings.BASE_DIR, app_name)
    os.makedirs(app_path, exist_ok=True)

    # Create necessary files for the new app
    open(os.path.join(app_path, '__init__.py'), 'w').close()
    open(os.path.join(app_path, 'models.py'), 'w').close()
    open(os.path.join(app_path, 'views.py'), 'w').close()
    open(os.path.join(app_path, 'urls.py'), 'w').close()
    open(os.path.join(app_path, 'admin.py'), 'w').close()


def generate_model_code(app_name, fields):
    code = f"from django.db import models\n\n\nclass {app_name.capitalize()}(models.Model):\n"
    for field in fields:
        code += f"    {field['name']} = models.{field['field_type']}("
        if field['field_type'] == 'CharField' and field.get('max_length'):
            code += f"max_length={field['max_length']}, "
        if not field['is_required']:
            code += "blank=True, null=True"
        code += ")\n"
    code += "\n    def __str__(self):\n"
    code += "        return self.name  # Replace with a more descriptive field if necessary\n"
    return code


def generate_crud_views_code(app_name):
    class_name = app_name.capitalize()
    views_code = f"""from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import {class_name}
from django.urls import reverse_lazy

class {class_name}ListView(ListView):
    model = {class_name}
    template_name = "{app_name}/{class_name.lower()}_list.html"

class {class_name}CreateView(CreateView):
    model = {class_name}
    fields = "__all__"
    template_name = "{app_name}/{class_name.lower()}_form.html"

class {class_name}UpdateView(UpdateView):
    model = {class_name}
    fields = "__all__"
    template_name = "{app_name}/{class_name.lower()}_form.html"

class {class_name}DeleteView(DeleteView):
    model = {class_name}
    template_name = "{app_name}/{class_name.lower()}_confirm_delete.html"
    success_url = reverse_lazy('{app_name}:{class_name.lower()}_list')
"""
    return views_code


# Generate URL paths for the CRUD views
def generate_crud_urls_code(app_name):
    class_name = app_name.capitalize()
    urls_code = f"""from django.urls import path
from .views import (
    {class_name}ListView,
    {class_name}CreateView,
    {class_name}UpdateView,
    {class_name}DeleteView
)

app_name = '{app_name}'

urlpatterns = [
    path('', {class_name}ListView.as_view(), name='{class_name.lower()}_list'),
    path('create/', {class_name}CreateView.as_view(), name='{class_name.lower()}_create'),
    path('<int:pk>/update/', {class_name}UpdateView.as_view(), name='{class_name.lower()}_update'),
    path('<int:pk>/delete/', {class_name}DeleteView.as_view(), name='{class_name.lower()}_delete'),
]
"""
    return urls_code

# Update settings.py to add the new app to INSTALLED_APPS
def update_settings(app_name):
    settings_file_path = os.path.join(settings.BASE_DIR, 'autoPilot', 'settings.py')
    
    with open(settings_file_path, 'r') as f:
        settings_content = f.read()

    if f"'{app_name}'," not in settings_content:
        new_content = settings_content.replace(
            "INSTALLED_APPS = [",
            f"INSTALLED_APPS = [\n    '{app_name}',"
        )
        
        with open(settings_file_path, 'w') as f:
            f.write(new_content)


def update_urls(app_name):
    urls_file_path = os.path.join(settings.BASE_DIR, 'autoPilot', 'urls.py')

    with open(urls_file_path, 'r') as f:
        urls_content = f.read()

    # Add the new app's urls.py include to the main urls.py
    include_statement = f"path('{app_name}/', include('{app_name}.urls')),"
    if include_statement not in urls_content:
        urls_content = urls_content.replace(
            "urlpatterns = [",
            f"urlpatterns = [\n    {include_statement}"
        )

        with open(urls_file_path, 'w') as f:
            f.write(urls_content)




logger = logging.getLogger(__name__)

def create_app(request):
    if request.method == "POST":
        app_form = GeneratedAppForm(request.POST)
        field_formset = ModelFieldFormSet(request.POST)

        if app_form.is_valid() and field_formset.is_valid():
            app = app_form.save()  # Save the GeneratedApp instance

            # Assign the app to the ModelField instances
            fields = field_formset.save(commit=False)
            for field in fields:
                field.app = app  # Set the related GeneratedApp instance
                field.save()  # Save each field

            # Generate app directory and necessary files
            create_app_directory(app.name)

            # Generate models.py based on the fields
            model_code = generate_model_code(app.name, [{
                "name": field.name,
                "field_type": field.field_type,
                "max_length": field.max_length,
                "is_required": field.is_required
            } for field in fields])

            models_file_path = os.path.join(settings.BASE_DIR, app.name, 'models.py')
            with open(models_file_path, 'w') as f:
                f.write(model_code)

            # Generate views.py with CRUD operations
            views_code = generate_crud_views_code(app.name)
            views_file_path = os.path.join(settings.BASE_DIR, app.name, 'views.py')
            with open(views_file_path, 'w') as f:
                f.write(views_code)

            # Generate urls.py for the CRUD views
            urls_code = generate_crud_urls_code(app.name)
            urls_file_path = os.path.join(settings.BASE_DIR, app.name, 'urls.py')
            with open(urls_file_path, 'w') as f:
                f.write(urls_code)

            # Update settings.py and project's main urls.py
            update_settings(app.name)
            update_urls(app.name)

            # Generate dynamic HTML templates
            generate_html_templates(app.name, fields)

            # Automatically run makemigrations and migrate
            try:
                logger.info(f"Running makemigrations for app: {app.name}")
                call_command("makemigrations", app.name)
                logger.info("makemigrations completed successfully.")

                logger.info("Running migrate")
                call_command("migrate")
                logger.info("migrate completed successfully.")
            except Exception as e:
                # Log the error and return a friendly message
                logger.error(f"Error during migrations: {e}")
                return HttpResponse(f"Error during migrations: {e}", status=500)

            return HttpResponse(f"App '{app.name}' created successfully with CRUD views, URLs, templates, and database migrations!")
    else:
        app_form = GeneratedAppForm()
        field_formset = ModelFieldFormSet(queryset=ModelField.objects.none())

    return render(request, "apphub/create_app.html", {
        "app_form": app_form,
        "field_formset": field_formset,
    })

def generate_html_templates(app_name, fields):
    # Path for templates directory
    templates_dir = os.path.join(settings.BASE_DIR, app_name, 'templates', app_name)
    os.makedirs(templates_dir, exist_ok=True)

    # Generate List view template
    list_template_code = generate_model_list_template(app_name, fields)
    with open(os.path.join(templates_dir, f'{app_name.lower()}_list.html'), 'w') as f:
        f.write(list_template_code)

    # Generate Form view template
    form_template_code = generate_model_form_template(app_name, fields)
    with open(os.path.join(templates_dir, f'{app_name.lower()}_form.html'), 'w') as f:
        f.write(form_template_code)

    # Generate Delete confirmation template
    delete_template_code = generate_model_delete_template(app_name)
    with open(os.path.join(templates_dir, f'{app_name.lower()}_confirm_delete.html'), 'w') as f:
        f.write(delete_template_code)


def generate_html_templates(app_name, fields):
    # Path for templates directory
    templates_dir = os.path.join(settings.BASE_DIR, app_name, 'templates', app_name)
    os.makedirs(templates_dir, exist_ok=True)

    # Generate List view template
    list_template_code = generate_model_list_template(app_name, fields)
    with open(os.path.join(templates_dir, f'{app_name.lower()}_list.html'), 'w') as f:
        f.write(list_template_code)

    # Generate Form view template
    form_template_code = generate_model_form_template(app_name, fields)
    with open(os.path.join(templates_dir, f'{app_name.lower()}_form.html'), 'w') as f:
        f.write(form_template_code)

    # Generate Delete confirmation template
    delete_template_code = generate_model_delete_template(app_name)
    with open(os.path.join(templates_dir, f'{app_name.lower()}_confirm_delete.html'), 'w') as f:
        f.write(delete_template_code)


def generate_model_list_template(app_name, fields):
    field_headers = "\n".join([f"                <th>{field.name.capitalize()}</th>" for field in fields])
    field_rows = "\n".join([f"                <td>{{{{ obj.{field.name} }}}}</td>" for field in fields])

    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{app_name.capitalize()} List</title>
</head>
<body>
    <h1>{app_name.capitalize()} List</h1>
    <table border="1">
        <thead>
            <tr>
{field_headers}
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {{% for obj in object_list %}}
            <tr>
{field_rows}
                <td>
                    <a href="{{{{ obj.pk }}}}/update/">Edit</a> |
                    <a href="{{{{ obj.pk }}}}/delete/">Delete</a>
                </td>
            </tr>
            {{% endfor %}}
        </tbody>
    </table>
    <a href="create/">Add New</a>
</body>
</html>
"""


def generate_model_form_template(app_name, fields):
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{app_name.capitalize()} Form</title>
</head>
<body>
    <h1>{app_name.capitalize()} Form</h1>
    <form method="post">
        {{% csrf_token %}}
        {{ form.as_p }}
        <button type="submit">Save</button>
    </form>
    <a href="/">Back to List</a>
</body>
</html>
"""


def generate_model_delete_template(app_name):
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Confirm Delete</title>
</head>
<body>
    <h1>Confirm Delete</h1>
    <p>Are you sure you want to delete this item?</p>
    <form method="post">
        {{% csrf_token %}}
        <button type="submit">Yes, Delete</button>
    </form>
    <a href="/">Cancel</a>
</body>
</html>
"""

