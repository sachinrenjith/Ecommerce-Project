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
      razorpay_payment_id = request.GET.get("razorpay_payment_id")
      order_number = request.GET.get("order_number")
      amount_paid = request.GET.get("amount_paid")


      try:
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
         print(cart_items)
         for item in cart_items:
             
             print("Product ID:", item.product_id)
             print("Quantity:", item.quantity)
             orderproduct = OrderProduct()
             orderproduct.order_id = order.id
             orderproduct.payment = payment
             orderproduct.user_id = request.user.id
             orderproduct.product_id = item.product_id
             orderproduct.quantity = item.quantity
             orderproduct.product_price = item.product.price
             orderproduct.ordered = True
             orderproduct.save()
             print(item)
             # Reduce The Qantity Of The Sold Products
             product = Product.objects.get(id=item.product_id)
             product.stock -= item.quantity
             product.save()

             order=Order.objects.get(order_number=order_number,is_ordered=True)
             ordered_products = OrderProduct.objects.filter(order_id=order.id)

             subtotal = 0
             for i in ordered_products:
                 subtotal += i.product_price * i.quantity


             payment = Payment.objects.get(razorpay_payment_id=razorpay_payment_id)

             context = {
                 'order': order,
                 'ordered_products':ordered_products,
                 'order_number':order.order_number,
                 'razorpay_payment_id':payment.razorpay_payment_id,
                 'payment':payment,
                 'subtotal':subtotal,
             }
             return render(request, 'orders/order_complete.html',context)

      except(Payment.DoesNotExist, Order.DoesNotExist):
          return redirect('home')
            


  








 







 