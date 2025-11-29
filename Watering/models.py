from django.db import models
from django.contrib.auth.models import AbstractUser, User

class User(AbstractUser):
    email = models.EmailField(unique=True, blank=False)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)

    def __str__(self):
        return self.username


# Create your models here.
class Item(models.Model):
    CATEGORY_CHOICES = [
        ('system', 'Системи автоматичного поливу'),
        ('sprinkles', 'Розбризкувачі'),
        ('pumps', 'Насоси'),
        ('hoses', 'Шланги'),
        ('valves', 'Клапани'),
        ('sensors', 'Датчики вологості'),
        ('controllers', 'Контролери'),
        ('filters', 'Фільтри'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(decimal_places=2, max_digits=10)
    image = models.ImageField("Зображення", upload_to='images/', blank=True, null=True)
    in_stock = models.BooleanField(default=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

class Kit(models.Model):
    name = models.TextField()
    description = models.TextField()
    items = models.ManyToManyField(Item, through='KitItem')
    image = models.ImageField("Зображення", upload_to='static/media/', blank=True, null=True)
    price = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name
    

class KitItem(models.Model):
    kit = models.ForeignKey(Kit, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість в наборі")

    def __str__(self):
        return f"{self.item.name} ({self.kit.name})"


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    
class UsersQuestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question_text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question from {self.user.username} at {self.submitted_at}"
    

class Comment(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    class Meta:
        ordering = ['created_at']
    
    def is_reply(self):
        return self.parent is not None
    

class Service(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  

    def __str__(self):
        return self.title
    
class ServiceOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(default='')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Замовлення {self.service.title} від {self.user.username}"

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField(default=0) 
    active = models.BooleanField(default=True)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    promo_code = models.ForeignKey(PromoCode, blank=True, null=True, on_delete=models.SET_NULL)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total_price(self):
        return sum([item.total_price for item in self.items.all()])


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.item.name} x{self.quantity}"

    @property
    def total_price(self):
        return self.item.price * self.quantity