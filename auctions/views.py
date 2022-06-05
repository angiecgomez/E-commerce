from io import RawIOBase

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import Bid, Comment, Listing, User, Watchlist


def index(request):
    products = Listing.objects.filter(status=True)
    for p in products:
        p.price = maximum_bid(p)
    return render(request, "auctions/index.html",{
        "products": products,
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def create(request):
    if request.method == "POST":
        p = Listing()
        p.title = request.POST["title"]
        p.description = request.POST["description"]
        p.price = request.POST["price"]
        p.image_url = request.POST["url"]
        p.category = request.POST["category"]
        p.seller = request.user
        p.save()
        return redirect("index")
    return render(request, "auctions/create.html")

def listing(request, id):
    product = Listing.objects.get(pk=id)
    current_bid = maximum_bid(product)
    comments = product.comment_set.all().order_by("-date")
    can_comment = False
    bid_message = "" 
    message={"type": None, "message": None}
    watchlist = None

    if request.user.is_authenticated:

        user = request.user
        can_comment = True
        watchlist = 0
        if user.watchlist.filter(product=product).exists():
            watchlist = 1

        if request.POST.get('current_bid') and product.status == True:
            user_bid = float(request.POST["current_bid"])
            if not user.bid.filter(product=product).exists():
                if user_bid > current_bid:
                    Bid.objects.create(product=product, bidder=user, bid=user_bid)
                    current_bid = user_bid
                    message={"type":"success", "message":"Accepted bid"}
                else:
                    message ={"type":"danger", "message": f"Bid not accepted. Your bid must be greater than: $ {current_bid}"}
            else:
                if user_bid > current_bid:
                    bid = user.bid.get(product=product)
                    bid.bid = user_bid
                    bid.save()
                    current_bid = user_bid
                    message={"type":"success", "message":"Updated bid"}
                else:
                    message ={"type":"danger", "message": f"Bid not accepted. Your bid must be greater than: $ {current_bid}"}

        if request.GET.get('close') == "true":
            if product.seller == request.user:
                product.status = False
                if product.bid_set.all().count()>0:
                    product.winner = product.bid_set.get(bid=current_bid).bidder
                product.save()
            return HttpResponseRedirect(reverse("listing", args=(product.id,)))

        if request.POST.get('comment'):
            comment = request.POST["comment"]
            Comment.objects.create(product=product, author=user, content=comment)
            return HttpResponseRedirect(reverse("listing", args=(product.id,)))

        if user.bid.filter(product=product).exists():
            bid_message = "Update your bid"
        else: 
            bid_message ="Place bid"

    return render(request, "auctions/listing.html", {
        "product": product,
        "bids": product.bid_set.all().count(),
        "current_bid": current_bid,
        "comments": comments,
        "message_type": message["type"],
        "message": message["message"],
        "categories": product.category,
        "can_comment": can_comment,
        "watchlist": watchlist,
        "bid_message": bid_message
    })

#function that returns the maximum bid#

def maximum_bid(product):
    bids = product.bid_set.all()
    price = product.price
    if bids.count()>0:
        highest_bid = bids.aggregate(Max('bid'))["bid__max"]
        price = highest_bid
    return price 

@login_required(login_url='/login')
def watchlist(request):
    user = User.objects.get(id=request.user.id)
    if request.GET.get('list') and request.GET.get('action'):
        list_id = int(request.GET['list'])
        action = request.GET['action']
        try:
            w = user.watchlist.filter(product=Listing.objects.get(id=list_id))
            if action == "add" and w.count() == 0:
                user.watchlist.create(product=Listing.objects.get(id=list_id))
            elif action == "remove" and w.count() == 1:
                w.delete()
            return HttpResponseRedirect(reverse('listing', args=[list_id,]))
        except:
            return HttpResponseRedirect(reverse('listing', args=[list_id,]))
    watchlist = Watchlist.objects.filter(user_wl=user)
    return render(request, "auctions/watchlist.html", {
        "watchlist": watchlist
    })

def categories(request):
    categories = Listing.objects.values('category').distinct()
    return render(request, "auctions/categories.html",{
        "categories": categories,
    })

def category(request, name):
    products = Listing.objects.filter(category=name)
    for p in products:
        p.price = maximum_bid(p)
    return render(request, "auctions/index.html",{
        "products": products,
        "category": name
    })
        



