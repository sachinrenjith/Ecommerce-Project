from django.shortcuts import render, redirect
import datetime
from carts.models import CartItem, Cart
from .forms import OrderForm
from .models import Payment,Order,OrderProduct
import razorpay
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from carts.models import Product
from django.db import transaction

# Create your views here.

# @transaction.atomic
def payment(request):
    # Assuming you receive the payment details as POST data
    razorpay_payment_id = request.GET.get("razorpay_payment_id")
    amount_paid = request.GET.get("amount_paid")
    razor_pay_status = request.GET.get("razor_pay_status")
    order_number = request.GET.get("order_number")
    print('llllllllllllllllllllllllllllllll')
    print(razor_pay_status,amount_paid,razorpay_payment_id)
     # Fetch the order based on the order_id and other relevant criteria
    order = get_object_or_404(Order, user=request.user, is_ordered=False, order_number=order_number)
    print(order)

    # Storing Transaction Details In Payment Model
    payment = Payment.objects.create(
        user=request.user,
        razorpay_payment_id=razorpay_payment_id,
        amount_paid=amount_paid,
        razorpay_status=razor_pay_status,
    )
    # payment.save()

    # Update the order's payment and is_ordered status
    order.payment = payment
    order.is_ordered = True
    order.save()
    
      # Move The Cart Items To Order Product Table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # Reduce The Qantity Of The Sold Products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

 

    # Clear Cart
    CartItem.objects.filter(user=request.user).delete()

    return render(request,'orders/payment.html')






def place_order(request, total=0, quantity=0):
    current_user = request.user
     
    # cart_items = CartItem.objects.filter(user=current_user)
    cart_items = CartItem.objects.all()
    cart_count = cart_items.count()
    
    # if cart_count <= 0:
    #     return redirect('checkout')
   
    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax

    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
             
            data = Order()
            data.user = current_user
            data.first_name =form.cleaned_data['first_name']
            data.last_name =form.cleaned_data['last_name']
            data.email =form.cleaned_data['email']
            data.phone_number =form.cleaned_data['phone_number']
            data.address_line_1 =form.cleaned_data['address_line_1']
            data.address_line_2 =form.cleaned_data['address_line_2']
            data.state =form.cleaned_data['state']
            data.city =form.cleaned_data['city']
            data.order_note =form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            
            data.save()
            
             
            # generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,mt)
            current_date =d.strftime("%Y%d%m")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            
            data.save()
            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)

            
           

            client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
            payment = client.order.create({'amount':int(grand_total)*100, 'currency': 'INR', 'payment_capture': 1})
            
            razorpay_id = settings.RAZOR_KEY_ID
            context ={
                'order':order,
                'cart_items':cart_items,
                'total':total,
                'tax':tax,
                'grand_total':grand_total,
                'payment': payment,
                'order_number':order_number,
            }
            return render(request,'orders/payment.html',context)  
        else:    
            return redirect('checkout')


def success(request):
    
    # Get the payment details from the request
    razorpay_payment_id = request.GET.get("razorpay_payment_id")
    razorpay_order_id = request.GET.get("razorpay_order_id")
    razor_pay_status = request.GET.get("razor_pay_status")
    amount_paid = request.GET.get("amount_paid")
    order_number = request.GET.get("order_number")
    full_name = request.GET.get("full_name")
    full_address = request.GET.get("full_address")
    state = request.GET.get("state")
    city= request.GET.get("city")

     
      # Storing Transaction Details In Payment Model
    payment = Payment.objects.create(
        user=request.user,
        razorpay_payment_id=razorpay_payment_id,
        amount_paid=amount_paid,
        razor_pay_status='Success',
        razorpay_order_id=order_number
    )

    order = get_object_or_404(Order, user=request.user, is_ordered=False, order_number=order_number)
    order.payment = payment
    order.is_ordered = True
    order.save()


     # Move The Cart Items To Order Product Table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # Reduce The Qantity Of The Sold Products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
   

    context = {
        "order_number": order_number,
        "amount_paid": amount_paid,
        "razorpay_payment_id": razorpay_payment_id,
        "full_name": full_name,
        "full_address":  full_address,
        "state": state,
        "city": city,
        
    }
    return render(request, "orders/order_complete.html", context)

    


  








 







 