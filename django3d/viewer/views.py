from django.shortcuts import render
from django.views.generic import DetailView
from .models import ModelModel, LiteModelModel


def demo(request):
    return render(request, 'viewer/index.html', {'model_path': '/static/obj/demo.obj'})


class ModelView(DetailView):
    model = ModelModel
    template_name = "viewer/index.html"
    context_object_name = "model"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_path'] = f'/static/obj/{self.object.pk}.obj'
        return context


class LiteModelView(DetailView):
    model = LiteModelModel

    def get_template_names(self):
        pk = self.kwargs['pk']
        template_name = f"viewer/sfm/{pk}/sfm_output.html"
        return [template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
