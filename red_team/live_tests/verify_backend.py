"""Run inside Django's shell; disposable fixtures are rolled back, not committed.

This tests Django request handlers against PostgreSQL, NOT browser/TLS/CSRF.
Use the HTTP regression runner separately for the deployed nginx path.
"""
import json
import uuid
import secrets
from decimal import Decimal
from datetime import datetime, timezone
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.test import Client
from products.models import Product, Category
from orders.models import Order, OrderItem
from carts.models import Cart, CartItem
from users.models import Coupon, CouponUsage
from audit.models import AuditLog
from rest_framework_simplejwt.tokens import AccessToken

rows = []
def check(test, passed, detail):
    rows.append(dict(test=test, status='TESTED - DEFENSE HELD' if passed else 'INCONCLUSIVE', detail=detail))

summary = dict(timestamp=datetime.now(timezone.utc).isoformat(), mode='Django Client + PostgreSQL, transaction rollback; not live HTTP or browser',
    tables=connection.introspection.table_names(),
    roles=list(User.objects.values('id', 'is_staff', 'is_superuser').order_by('id')),
    order_owners=list(Order.objects.values('id', 'user_id').order_by('id')),
    password_algorithms=sorted({u.password.split('$')[0] for u in User.objects.all()}))
prefix = 'rt_' + uuid.uuid4().hex[:12]
with transaction.atomic():
    fixture_password = secrets.token_urlsafe(32)
    alice = User.objects.create_user(username=prefix+'a', password=fixture_password)
    bob = User.objects.create_user(username=prefix+'b')
    category = Category.objects.create(name=prefix)
    product = Product.objects.create(name=prefix, category=category, price=Decimal('100'), stock=20)
    coupon = Coupon.objects.create(code=prefix.upper(), discount_percent=10)
    profile = alice.profile
    profile.store_credit = Decimal('1000'); profile.save()
    cart = Cart.objects.create(user=alice)
    foreign = Order.objects.create(user=bob)
    OrderItem.objects.create(order=foreign, product=product, quantity=1, price=100)
    c = Client(HTTP_HOST='localhost', secure=True)
    c.force_login(alice)
    c.defaults['HTTP_AUTHORIZATION'] = 'Bearer ' + str(AccessToken.for_user(alice))
    def req(method, path, data=None):
        if method == 'get':
            return c.get(path, secure=True)
        return getattr(c, method)(path, data=json.dumps(data or {}), content_type='application/json', secure=True)
    before = Order.objects.count()
    r = req('get', '/api/orders/orders/'+str(foreign.id)+'/')
    check('DB-IDOR-detail', r.status_code == 404 and str(foreign.id).encode() not in r.content,
          {'status':r.status_code, 'foreign_order':foreign.id, 'owner':bob.id, 'attacker':alice.id})
    r = req('get','/api/orders/orders/')
    payload=r.json(); entries=payload.get('results',[]) if isinstance(payload,dict) else payload
    check('DB-IDOR-list', r.status_code==200 and all(x['user']==alice.id for x in entries), {'status':r.status_code,'entries':entries})
    for quantity in [-1, 0, 'invalid']:
        r=req('post','/api/carts/cart/add/',{'product':product.id,'quantity':quantity})
        check('DB-quantity-'+str(quantity),r.status_code==400 and not cart.items.exists(), {'status':r.status_code,'body':r.json(),'cart_items':cart.items.count()})
    r=req('post','/api/orders/order-items/',{'product':product.id,'quantity':1,'price':'0.01'})
    check('DB-price-item-role',r.status_code==403 and Order.objects.count()==before,{'status':r.status_code,'body':r.json()})
    # A separate order-create route can have different security properties.
    credit_before=alice.profile.store_credit
    r=req('post','/api/orders/orders/',{'status':'Completed','items':[{'product':product.id,'quantity':1,'price':'0.01'}]})
    created=Order.objects.filter(user=alice).last()
    if created:
        item=created.items.first(); profile.refresh_from_db()
        check('DB-order-server-price',item.price==product.price and created.status=='Pending',
              {'status':r.status_code,'stored_price':str(item.price),'stored_status':created.status})
        # Record behavior without assuming a Pending order is proof of payment bypass.
        rows.append(dict(test='DB-direct-order-workflow',status='INCONCLUSIVE',detail={'http':r.status_code,'stored_status':created.status,'credit_debited':str(credit_before-profile.store_credit),'note':'Pending order created without debit; fulfillment/payment semantics require review.'}))
    else:
        rows.append(dict(test='DB-order-server-price',status='INCONCLUSIVE',detail={'status':r.status_code,'body':r.json()}))
    CartItem.objects.create(cart=cart,product=product,quantity=1)
    r=req('post','/api/carts/orders/checkout/',{'use_store_credit':False})
    check('DB-checkout-no-payment',r.status_code==400 and cart.items.count()==1,{'status':r.status_code,'body':r.json()})
    r=req('post','/api/carts/orders/checkout/',{'coupon_code':coupon.code})
    profile.refresh_from_db(); product.refresh_from_db()
    initial_usage=CouponUsage.objects.filter(user=alice,coupon=coupon).count()
    first=dict(status=r.status_code,body=r.json(),credit=str(profile.store_credit),stock=product.stock,usage=initial_usage)
    CartItem.objects.create(cart=cart,product=product,quantity=1)
    credit=profile.store_credit; stock=product.stock; orders=Order.objects.count()
    r=req('post','/api/carts/orders/checkout/',{'coupon_code':coupon.code})
    profile.refresh_from_db(); product.refresh_from_db()
    check('DB-coupon-replay',first['status']==200 and initial_usage==1 and r.status_code==400 and profile.store_credit==credit and product.stock==stock and Order.objects.count()==orders,
          {'first':first,'second_status':r.status_code,'second_body':r.json(),'credit_unchanged':profile.store_credit==credit,'stock_unchanged':product.stock==stock})
    profile.store_credit=0; profile.save()
    r=req('post','/api/carts/orders/checkout/',{})
    check('DB-insufficient-credit',r.status_code==400 and Order.objects.count()==orders,{'status':r.status_code,'body':r.json()})
    profile.store_credit=1000; profile.save(); product.stock=0; product.save()
    r=req('post','/api/carts/orders/checkout/',{})
    check('DB-insufficient-stock',r.status_code==400 and Order.objects.count()==orders,{'status':r.status_code,'body':r.json()})
    r=req('get','/admin/users/newslettersubscriber/')
    check('DB-customer-admin',r.status_code==302 and '/admin/login/' in r.get('Location',''),{'status':r.status_code,'location':r.get('Location')})
    summary['fixture_audit_actions']=list(AuditLog.objects.filter(user=alice).values('action','path'))
    # Lab 2 exceptional input: registration must reject an overlong email,
    # rather than silently truncate it into a privileged domain.
    long_email = 'x'*260 + '@example.test'
    count=User.objects.count()
    r=req('post','/api/users/signup/',{'username':prefix+'long','email':long_email,'password':fixture_password})
    check('DB-overlong-registration',r.status_code==400 and User.objects.count()==count,{'status':r.status_code,'body':r.json(),'user_count_unchanged':User.objects.count()==count})
    # Enroll only the disposable user. Compare browser-session and JWT MFA paths.
    from users.totp import generate_totp_secret, get_totp_code
    profile.totp_enabled=True; profile.totp_secret=generate_totp_secret(); profile.save()
    anonymous=Client(HTTP_HOST='localhost')
    r=anonymous.post('/api/auth/login/',data=json.dumps({'username':alice.username,'password':fixture_password}),content_type='application/json',secure=True)
    tokens=r.json()
    protected=anonymous.get('/api/orders/orders/',HTTP_AUTHORIZATION='Bearer '+tokens.get('access',''),secure=True)
    bypass=r.status_code==200 and bool(tokens.get('access')) and protected.status_code==200
    rows.append(dict(test='DB-MFA-JWT-bypass',status='CONFIRMED VULNERABILITY' if bypass else 'INCONCLUSIVE',detail={'totp_enabled':True,'password_only_status':r.status_code,'access_token_issued':bool(tokens.get('access')),'protected_orders_status':protected.status_code,'no_totp_submitted':True}))
    session_client=Client(HTTP_HOST='localhost')
    session=session_client.session; session['pre_2fa_user_id']=alice.id; session['pre_2fa_backend']='django.contrib.auth.backends.ModelBackend'; session.save()
    valid=get_totp_code(profile.totp_secret)
    invalid='000000' if valid!='000000' else '111111'
    r=session_client.post('/dashboard/2fa/verify/',{'code':invalid,'verify':bob.id,'user_id':bob.id},secure=True)
    check('DB-MFA-forged-identity', '_auth_user_id' not in session_client.session,{'status':r.status_code,'authenticated': '_auth_user_id' in session_client.session,'target_user':bob.id})
    r=session_client.post('/dashboard/2fa/verify/',{'code':valid},secure=True)
    check('DB-MFA-correct-identity',str(session_client.session.get('_auth_user_id'))==str(alice.id),{'status':r.status_code,'authenticated_user':session_client.session.get('_auth_user_id'),'expected':alice.id})
    transaction.set_rollback(True)
summary['rollback_verified']=not User.objects.filter(username__startswith=prefix).exists() and not Product.objects.filter(name=prefix).exists()
summary['results']=rows
print('RED_TEAM_JSON:'+json.dumps(summary,default=str))
