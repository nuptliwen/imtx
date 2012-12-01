from django.template import RequestContext
from django.views.decorators.http import require_GET
from django.shortcuts import render_to_response

from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.pdt.models import PayPalPDT
from paypal.standard.pdt.forms import PayPalPDTForm

from manity.forms import PurchaserForm

def index(request):
    return render_to_response("index.html", {'form': PurchaserForm()})

def purchase(request):
    # What you want the button to do.
    paypal_dict = {
        "business": "tualat_1353483092_biz@gmail.com",
        "amount": "5.00",
        "item_name": "Manity License",
        "invoice": "me.imtx.manity.license",
        "notify_url": request.build_absolute_uri('/manity/paypal/pdt/'),
        "return_url": request.build_absolute_uri('/manity/paypal/pdt/'),
        "cancel_return": request.build_absolute_uri('/manity/'),
    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}
    return render_to_response("payment.html", context)

@require_GET
def pdt(request, item_check_callable=None, template="pdt/pdt.html", context=None):
    """Payment data transfer implementation: http://tinyurl.com/c9jjmw"""
    context = context or {}
    pdt_obj = None
    txn_id = request.GET.get('tx')
    failed = False
    if txn_id is not None:
        # If an existing transaction with the id tx exists: use it
        try:
            pdt_obj = PayPalPDT.objects.get(txn_id=txn_id)
        except PayPalPDT.DoesNotExist:
            # This is a new transaction so we continue processing PDT request
            pass

        if pdt_obj is None:
            form = PayPalPDTForm(request.GET)
            if form.is_valid():
                try:
                    pdt_obj = form.save(commit=False)
                except Exception, e:
                    error = repr(e)
                    failed = True
            else:
                error = form.errors
                failed = True

            if failed:
                pdt_obj = PayPalPDT()
                pdt_obj.set_flag("Invalid form. %s" % error)

            pdt_obj.initialize(request)

            if not failed:
                # The PDT object gets saved during verify
                pdt_obj.verify(item_check_callable)
    else:
        pass # we ignore any PDT requests that don't have a transaction id

    context.update({"failed":failed, "pdt_obj":pdt_obj})
    return render_to_response(template, context, RequestContext(request))
