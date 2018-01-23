from django.views.generic import ListView

from opentech.apply.funds.models import ApplicationSubmission

from .tables import DashboardTable


class DashboardView(ListView):
    model = ApplicationSubmission
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = DashboardTable(context['object_list'])
        return context
