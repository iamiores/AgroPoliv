from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('articles/', views.articles, name='articles'),
    path('submit_question/', views.submit_question, name='submit_question'),
    path('articles/<int:article_id>/', views.article_detail, name='article_detail'),
    path('article/<int:article_id>/add_comment/', views.add_comment, name='add_comment'),
    path('catalog/', views.catalog, name='catalog'),
    path('logout/', views.logout_view, name='logout'),
    path("services/", views.services, name="services"),
    path("services/order/", views.order_service, name="order_service"),
    path("cart/", views.cart, name="cart"),
    path("cart/update/<int:cart_item_id>/", views.update_cart_item, name="update_cart_item"), 
    path("cart/remove/<int:cart_item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/clear/", views.clear_cart, name="clear_cart"),
    path('item/<int:item_id>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('item/<int:item_id>/', views.item_detail, name='item_detail'),
    path('item/<int:item_id>/buy/', views.buy_item, name='buy_item'),
    path('promo/validate/', views.validate_promo, name='validate_promo'),
    path('cart/checkout/selected/', views.checkout_selected, name='checkout_selected'),
    path('interactive_board/', views.interactive_board, name='interactive_board'),
    path('interactive_board/add_to_cart/', views.add_board_item, name='add_board_item'),
    path("verify/<int:user_id>/", views.verify_email, name="verify_email"),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])