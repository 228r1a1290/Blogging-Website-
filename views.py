from django.shortcuts import render,redirect
from django.contrib.auth.models import User,auth
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import *

from .models import Comment, Post, PostView
# Create your views here.
def index(request):
    return render(request,"index.html",{
        'posts':Post.objects.filter(user_id=request.user.id).order_by("id").reverse(),
        'top_posts':Post.objects.all().order_by("-likes"),
        'recent_posts':Post.objects.all().order_by("-id"),
        'user':request.user,
        'media_url':settings.MEDIA_URL
    })


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password == password2:
            if User.objects.filter(username=username).exists():
                messages.info(request,"Username already Exists")
                return redirect('signup')
            if User.objects.filter(email=email).exists():
                messages.info(request,"Email already Exists")
                return redirect('signup')
            else:
                User.objects.create_user(username=username,email=email,password=password).save()
                return redirect('signin')
        else:
            messages.info(request,"Password should match")
            return redirect('signup')
            
    return render(request,"signup.html")

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request,username=username,password=password)
        if user is not None:
            auth.login(request,user)
            return redirect("index")
        else:
            messages.info(request,'Username or Password is incorrect')
            return redirect("signin")
            
    return render(request,"signin.html")

def logout(request):
    auth.logout(request)
    return redirect('index')

def blog(request):
    return render(request,"blog.html",{
            'posts':Post.objects.filter(user_id=request.user.id).order_by("id").reverse(),
            'top_posts':Post.objects.all().order_by("-likes"),
            'recent_posts':Post.objects.all().order_by("-id"),
            'user':request.user,
            'media_url':settings.MEDIA_URL
        })
    
def create(request):
    if request.method == 'POST':
        try:
            postname = request.POST['postname']
            content = request.POST['content']
            category = request.POST['category']
            image = request.FILES['image']
            Post(postname=postname,content=content,category=category,image=image,user=request.user).save()
        except:
            print("Error")
        return redirect('index')
    else:
        return render(request,"create.html")
    
def profile(request,id):
    
    return render(request,'profile.html',{
        'user':User.objects.get(id=id),
        'posts':Post.objects.all(),
        'media_url':settings.MEDIA_URL,
    })
    
    
def profileedit(request,id):
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']
    
        user = User.objects.get(id=id)
        user.first_name = firstname
        user.email = email
        user.last_name = lastname
        user.save()
        return profile(request,id)
    return render(request,"profileedit.html",{
        'user':User.objects.get(id=id),
    })
    
def increaselikes(request,id):
    if request.method == 'POST':
        post = Post.objects.get(id=id)
        post.likes += 1
        post.save() 
    return redirect("index")


def post(request,id):
    post = Post.objects.get(id=id)
    
    # Increment view count
    post.views += 1
    post.save()
    
    # Record view for analytics
    if request.user.is_authenticated:
        # Create a PostView record
        view, created = PostView.objects.get_or_create(
            post=post,
            viewer=request.user,
            view_date__date=timezone.now().date()
        )
        # We'll update time_spent via JavaScript in the template
    
    return render(request,"post-details.html",{
        "user":request.user,
        'post':Post.objects.get(id=id),
        'recent_posts':Post.objects.all().order_by("-id"),
        'media_url':settings.MEDIA_URL,
        'comments':Comment.objects.filter(post_id = post.id),
        'total_comments': len(Comment.objects.filter(post_id = post.id)),
        'post_id': id  # Pass post ID for time tracking
    })
    
def savecomment(request,id):
    post = Post.objects.get(id=id)
    if request.method == 'POST':
        content = request.POST['message']
        Comment(post_id = post.id,user_id = request.user.id, content = content).save()
        return redirect("index")
    
def deletecomment(request,id):
    comment = Comment.objects.get(id=id)
    postid = comment.post.id
    comment.delete()
    return post(request,postid)
    
def editpost(request,id):
    post = Post.objects.get(id=id)
    if request.method == 'POST':
        try:
            postname = request.POST['postname']
            content = request.POST['content']
            category = request.POST['category']
            
            post.postname = postname
            post.content = content
            post.category = category
            post.save()
        except:
            print("Error")
        return profile(request,request.user.id)
    
    return render(request,"postedit.html",{
        'post':post
    })
    
def deletepost(request,id):
    Post.objects.get(id=id).delete()
    return profile(request,request.user.id)


def contact_us(request):
    context={}
    if request.method == 'POST':
        name=request.POST.get('name')    
        email=request.POST.get('email')  
        subject=request.POST.get('subject')  
        message=request.POST.get('message')  

        obj = Contact(name=name,email=email,subject=subject,message=message)
        obj.save()
        context['message']=f"Dear {name}, Thanks for your time!"

    return render(request,"contact.html")

@login_required
def update_time_spent(request, post_id):
    if request.method == 'POST':
        time_spent = request.POST.get('time_spent')
        if time_spent:
            try:
                post = Post.objects.get(id=post_id)
                view, created = PostView.objects.get_or_create(
                    post=post,
                    viewer=request.user,
                    view_date__date=timezone.now().date()
                )
                view.time_spent = int(time_spent)
                view.save()
                return redirect('post', id=post_id)
            except Post.DoesNotExist:
                pass
    return redirect('index')

@login_required
def dashboard(request):
    # Get user's posts
    user_posts = Post.objects.filter(user=request.user)
    
    # Calculate analytics
    total_views = user_posts.aggregate(Sum('views'))['views__sum'] or 0
    total_likes = user_posts.aggregate(Sum('likes'))['likes__sum'] or 0
    total_comments = Comment.objects.filter(post__in=user_posts).count()
    
    # Get time spent data
    post_views = PostView.objects.filter(post__in=user_posts)
    total_time_spent = post_views.aggregate(Sum('time_spent'))['time_spent__sum'] or 0
    
    # Get view data for the last 7 days
    last_week = timezone.now() - timedelta(days=7)
    daily_views = []
    
    for i in range(7):
        day = last_week + timedelta(days=i)
        day_views = post_views.filter(view_date__date=day.date()).count()
        daily_views.append({
            'date': day.strftime('%d %b'),
            'views': day_views
        })
    
    # Get top posts by views
    top_posts = user_posts.order_by('-views')[:5]
    
    # Get top posts by likes
    top_liked_posts = user_posts.order_by('-likes')[:5]
    
    # Get top posts by comments
    posts_with_comment_count = []
    for post in user_posts:
        comment_count = Comment.objects.filter(post=post).count()
        posts_with_comment_count.append({
            'post': post,
            'comment_count': comment_count
        })
    
    # Sort by comment count
    posts_with_comment_count.sort(key=lambda x: x['comment_count'], reverse=True)
    top_commented_posts = posts_with_comment_count[:5]
    
    context = {
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_time_spent': total_time_spent,
        'daily_views': daily_views,
        'top_posts': top_posts,
        'top_liked_posts': top_liked_posts,
        'top_commented_posts': top_commented_posts,
        'media_url': settings.MEDIA_URL,
    }
    
    return render(request, 'dashboard.html', context)
