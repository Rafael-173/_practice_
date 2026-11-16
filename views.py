from django.shortcuts import render

from .models import Category, StudyGroup


def index(request):
    
    categories = Category.objects.filter(code__in=("A", "B")).order_by("code")
    groups = (
        StudyGroup.objects.select_related("category", "branch")
        .order_by("start_date")[:3]
    )

    return render(
        request,
        "index.html",
        {
            "categories": categories,
            "groups": groups,
        },
    )
