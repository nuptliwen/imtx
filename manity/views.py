from django.shortcuts import render_to_response
from paypal.standard.forms import PayPalPaymentsForm

def index(request):
    return render_to_response("index.html")

def purchase(request):
    # What you want the button to do.
    paypal_dict = {
        "business": "tualat_1353483092_biz@gmail.com",
        "amount": "5.00",
        "item_name": "Manity License",
        "invoice": "me.imtx.manity.license",
        "notify_url": request.build_absolute_uri('/paypal/pdt/'),
        "return_url": request.build_absolute_uri('/paypal/pdt/'),
        "cancel_return": request.build_absolute_uri('/paypal/pdt/'),
    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}
    return render_to_response("payment.html", context)

