from django.shortcuts import render
from django.shortcuts import redirect
from . import models
from . import forms
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from captcha.models import CaptchaStore
from captcha.helpers import  captcha_image_url
from django.http import HttpResponse
import hashlib
import datetime
import json

# Create your views here.


def login(request):
    if request.session.get('is_login', None):
        return redirect("/index/")
    if request.method == "POST":
        login_form = forms.UserForm(request.POST)
        message = '请检查填写的内容!'
        # print(login_form)
        # print(request.POST)
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')
            capt = request.POST.get("captcha", None)
            key = request.POST.get("hashkey", None)
            try:
                user = models.User.objects.get(username=username)
            except:
                message = '用户不存在！'
                new_captcha = captcha()
                return render(request, 'login/login.html', locals())
            if not judge_captcha(capt, key):
                message = '验证码不正确'
                new_captcha = captcha()
                return render(request, 'login/login.html', locals())
            if not user.user_confirmed:
                message = '该用户未邮件确认，请确认后登陆！'
                new_captcha = captcha()
                return render(request, 'login/login.html', locals())
            if user.passwd == hash_code(password):
                request.session['is_login'] = True
                request.session['user_id'] = user.id
                request.session['user_name'] = user.username
                return redirect('/index/')
            else:
                message = '密码不正确!'
                new_captcha = captcha()
                return render(request, 'login/login.html', locals())

        else:
            # message = '验证码不正确'
            new_captcha = captcha()
            return render(request, 'login/login.html', locals())
    login_form = forms.UserForm()
    new_captcha = captcha()
    return render(request, 'login/login.html', locals())


def index(request):
    if not request.session.get('is_login', None):
        return redirect('/login/')
    return render(request, 'login/index.html')


def register(request):
    if request.session.get('is_login', None):
        return redirect('/index/')
    if request.method == 'POST':
        register_form = forms.RegisterForm(request.POST)
        message = '请检查填写的内容'
        if register_form.is_valid():
            # print(register_form)
            # print(request.POST)
            user_name = register_form.cleaned_data.get('username')
            password = register_form.cleaned_data.get('password')
            confirm_password = register_form.cleaned_data.get('confirm_password')
            email = register_form.cleaned_data.get('email')
            sex = register_form.cleaned_data.get('sex')
            capt = request.POST.get("captcha", None)
            key = request.POST.get("hashkey", None)
            if password != confirm_password:
                message = '两次输入的密码不一致'
                new_captcha = captcha()
                return render(request, 'login/register.html', locals())
            else:
                is_repeated_name = models.User.objects.filter(username=user_name)
                if is_repeated_name:
                    message = '此用户名已存在'
                    new_captcha = captcha()
                    return render(request, 'login/register.html', locals())
                is_same_email = models.User.objects.filter(email=email)
                if is_same_email:
                    message = '此邮箱已注册'
                    new_captcha = captcha()
                    return render(request, 'login/register.html', locals())
                if not judge_captcha(capt, key):
                    message = '验证码不正确'
                    new_captcha = captcha()
                    return render(request, 'login/register.html', locals())
            new_user = models.User()
            new_user.username = user_name
            new_user.passwd = hash_code(password)
            new_user.email = email
            new_user.sex = sex
            new_user.save()
            confirm_code = make_confirm_code(new_user)
            try:
                send_mail(email, confirm_code, new_user.username)
                message = '请前往注册邮箱进行确认后登陆！'
                return render(request, 'login/confirm.html', locals())
            except:
                message = '你输入的邮箱不存在或者邮件发送失败,请重新注册'
                new_user.delete()
                new_captcha = captcha()
                return render(request, 'login/register.html', locals())

        else:
            new_captcha = captcha()
            return render(request, 'login/register.html', locals())
    new_captcha = captcha()
    register_form = forms.RegisterForm()
    return render(request, 'login/register.html', locals())


def logout(request):
    if not request.session.get('is_login', None):
        return redirect("/login/")
    request.session.flush()
    return redirect("/login/")


def user_confirm(request):
    code = request.GET.get('code', None)
    message = ''
    try:
        new_confirm_user = models.ConfirmUser.objects.get(confirm_code=code)
    except:
        message = '无效的确认请求！'
        return render(request,'login/confirm.html', locals())
    create_time = new_confirm_user.create_time
    now = datetime.datetime.now()
    if now > create_time + datetime.timedelta(settings.CONFIRM_DAYS):
        new_confirm_user.user.delete()
        message = '您的邮件已经过期！请重新注册!'
        return render(request, 'login/confirm.html', locals())
    else:
        new_confirm_user.user.user_confirmed = True
        new_confirm_user.user.save()
        new_confirm_user.delete()
        message = '感谢确认，现在你可以正常登陆了！'
        return render(request,'login/confirm.html', locals())


def hash_code(s, salt='@#<>/df9dfj2dfdkf'):
    h = hashlib.sha256()
    s = s + salt
    h.update(s.encode())
    return h.hexdigest()


def make_confirm_code(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.username, now)
    models.ConfirmUser.objects.create(confirm_code=code, user=user,)
    return code


def send_mail(email, code, username):
    subject = '来自本地注册的确认邮件'
    text_content = '''感谢注册，如果你看到这条消息，说明你的邮箱不支持HTML链接功能，请联系管理员1'''
    html_content = '''亲爱的{},感谢注册<a href="http://{}/confirm/?code={}" target=blank>www.baidu.com</a>,<p>请点击站点链接完成注册确认!</p>
    <p>此链接有效期为{}天</p>'''.format(username, '127.0.0.1:8000', code, settings.CONFIRM_DAYS)
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


# 创建验证码
def captcha():
    hashkey = CaptchaStore.generate_key()   # 验证码答案
    image_url = captcha_image_url(hashkey)  # 验证码地址
    captcha = {'hashkey': hashkey, 'image_url': image_url}
    return captcha


# 刷新验证码
def refresh_captcha(request):
    return HttpResponse(json.dumps(captcha()), content_type='application/json')


# 验证验证码
def judge_captcha(captchaStr, captchaHashkey):
    if captchaStr and captchaHashkey:
        try:
            # 获取根据hashkey获取数据库中的response值
            get_captcha = CaptchaStore.objects.get(hashkey=captchaHashkey)
            if get_captcha.response == captchaStr.lower():
                return True
        except:
            return False
    else:
        return False

