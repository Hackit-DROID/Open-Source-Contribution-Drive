from django.contrib import admin
from .models import Book, StudentExtra, IssuedBook
import sys
import os

# Import State Machine & Multi-Agent Graph components from manage.py
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from manage import execute_async_agent_graph, AgentGraphState, GraphStatus, StateSchema
except ImportError:
    execute_async_agent_graph = None
    AgentGraphState = None
    GraphStatus = None
    StateSchema = None


class AgentGraphAdminMixin:
    """Admin mixin to integrate Asynchronous Multi-Agent Graph State Machine execution & recovery tracking."""

    @admin.action(description="Trigger Resilient Agent Graph Invoice Extraction")
    def run_agent_graph_extraction(self, request, queryset):
        if not execute_async_agent_graph:
            self.message_user(request, "Agent Graph State Machine module unavailable.", level="ERROR")
            return

        success_count = 0
        fallback_count = 0
        failed_count = 0

        for item in queryset:
            input_data = {
                "invoice_id": getattr(item, "id", "INV-ADMIN"),
                "vendor": getattr(item, "name", "Library Admin Request"),
                "total_amount": 100.0,
            }
            state = execute_async_agent_graph(input_data)
            if state.status == GraphStatus.SUCCESS:
                success_count += 1
            elif state.status == GraphStatus.FALLBACK_SUCCESS:
                fallback_count += 1
            else:
                failed_count += 1

        msg = f"Agent Graph Execution Complete: {success_count} Success, {fallback_count} Fallback Recovered, {failed_count} Failed."
        self.message_user(request, msg)


class BookAdmin(admin.ModelAdmin, AgentGraphAdminMixin):
    actions = ["run_agent_graph_extraction"]


admin.site.register(Book, BookAdmin)


class StudentExtraAdmin(admin.ModelAdmin):
    pass


admin.site.register(StudentExtra, StudentExtraAdmin)


class IssuedBookAdmin(admin.ModelAdmin):
    pass


admin.site.register(IssuedBook, IssuedBookAdmin)
