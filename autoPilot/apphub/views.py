from django.shortcuts import render, redirect
from django.conf import settings
import os
from .forms import GeneratedAppForm, ModelFieldFormSet
from django.http import HttpResponse
from .models import GeneratedApp, ModelField

def index(request):
    return HttpResponse("Welcome to the AppHub!")


# Helper functions
def create_app_directory(app_name):
    app_path = os.path.join(settings.BASE_DIR, app_name)
    os.makedirs(app_path, exist_ok=True)

    # Create necessary files
    open(os.path.join(app_path, '__init__.py'), 'w').close()
    open(os.path.join(app_path, 'models.py'), 'w').close()
    open(os.path.join(app_path, 'views.py'), 'w').close()
    open(os.path.join(app_path, 'urls.py'), 'w').close()
    open(os.path.join(app_path, 'admin.py'), 'w').close()

def generate_model_code(fields):
    code = "from django.db import models\n\nclass GeneratedModel(models.Model):\n"
    for field in fields:
        code += f"    {field['name']} = models.{field['field_type']}("
        if field['field_type'] == 'CharField' and field['max_length']:
            code += f"max_length={field['max_length']}, "
        if not field['is_required']:
            code += "blank=True, null=True"
        code += ")\n"
    return code

def generate_views_code():
    return """from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import GeneratedModel

class GeneratedModelListView(ListView):
    model = GeneratedModel
    template_name = "generated_model_list.html"

class GeneratedModelCreateView(CreateView):
    model = GeneratedModel
    fields = "__all__"
    template_name = "generated_model_form.html"
"""

def create_app(request):
    if request.method == "POST":
        app_form = GeneratedAppForm(request.POST)
        field_formset = ModelFieldFormSet(request.POST)

        if app_form.is_valid() and field_formset.is_valid():
            app = app_form.save()
            fields = field_formset.save(commit=False)

            # Generate app directory
            create_app_directory(app.name)

            # Generate models.py
            model_code = generate_model_code([{
                "name": field.name,
                "field_type": field.field_type,
                "max_length": field.max_length,
                "is_required": field.is_required
            } for field in fields])

            with open(os.path.join(settings.BASE_DIR, app.name, 'models.py'), 'w') as f:
                f.write(model_code)

            # Generate views.py
            with open(os.path.join(settings.BASE_DIR, app.name, 'views.py'), 'w') as f:
                f.write(generate_views_code())

            return HttpResponse(f"App {app.name} created successfully!")

    else:
        app_form = GeneratedAppForm()
        field_formset = ModelFieldFormSet(queryset=ModelField.objects.none())

    return render(request, "apphub/create_app.html", {
        "app_form": app_form,
        "field_formset": field_formset,
    })


