from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Listing(models.Model):
    title = models.CharField(max_length=60)
    description = models.TextField()
    price = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    image_url = models.CharField(max_length=350, null=True, blank=True)
    category = models.CharField(max_length=50)
    status = models.BooleanField(default=True)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listing")
    winner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="buy")

    def __str__(self):
        return self.title
    
class Comment (models.Model):
    product = models.ForeignKey(Listing, on_delete=models.CASCADE)
    content = models.TextField(null=False)
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product}" "    |    Comentario: " f"{self.content}"

class Bid(models.Model):
    product = models.ForeignKey(Listing, on_delete=models.CASCADE)
    bid = models.FloatField()
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bid")

    def __str__(self):
        return f"{self.product}"

class Watchlist(models.Model):
    product = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user_wl = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist")

    def __str__(self):
        return f"{self.user_wl}"

