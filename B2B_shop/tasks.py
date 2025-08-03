from celery import shared_task
from django.db import transaction
from .models import Seller, TransactionLog, Charge
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_charge_task(seller_id, amount_str, phone_number):
    """
    Celery task to process a charge asynchronously.
    This handles the database logic, ensuring the API can return quickly.
    """
    print("\n\n\n")
    print('in the task\n')
    amount = Decimal(amount_str)
    print('amount:', amount)
    try:
        with transaction.atomic():
            seller = Seller.objects.select_for_update().get(pk=seller_id)
            print('seller: ', seller.name)
            print('seller.credit: ', seller.credit)

            if seller.credit < amount:
                print('seller.credit < amount is TRUE')
                Charge.objects.create(
                    seller=seller,
                    phone_number=phone_number,
                    amount=amount,
                    status="failed"
                    )
                logger.warning("Charge failed for seller [%s]: insufficient credit (%s)", seller_id, amount)
                return ("Charge failed for seller [%s]: insufficient credit (%s)", seller_id, amount)

            charge = Charge.objects.create(
                seller=seller,
                phone_number=phone_number,
                amount=amount,
                status="completed" # i assume that charging is working well
            )

            new_balance = seller.credit - amount
            print("new_balance: ", new_balance)

            # get or Create log and update seller credit
            TransactionLog.objects.create(
                seller=seller,
                transaction_type='charge_sale',
                amount=-amount,
                balance_after=new_balance, 
                phone_number=phone_number
            )


            seller.credit = new_balance
            seller.save()
            print('seller saved\n')
            print('seller.credit: ', seller.credit)
            print("\n\n\n")

            return (f"Charge successful for {phone_number}. amount: {amount}")
            
    except Seller.DoesNotExist:
        return (f"Charge failed for {seller_id}: Seller not found.")
    except Exception as e:
        # The transaction will roll back automatically on error.
        return (f"An unexpected error occurred during charge for seller {seller_id}: {e}")