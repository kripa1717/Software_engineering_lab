from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('inventory/', views.inventory_list_view, name='inventory_list'),
    path('inventory/add/', views.add_item_view, name='add_item'),
    path('inventory/<int:item_id>/update-stock/', views.update_stock_view, name='update_stock'),

    path('alerts/', views.alert_list_view, name='alert_list'),
    path('alerts/<int:alert_id>/read/', views.mark_alert_read_view, name='mark_alert_read'),

    path('forecast/', views.forecast_view, name='forecast'),

    path('vendors/', views.vendor_list_view, name='vendor_list'),

    path('orders/', views.order_list_view, name='order_list'),
    path('orders/<int:order_id>/confirm/', views.confirm_delivery_view, name='confirm_delivery'),

    path('reports/', views.report_view, name='report'),
]
