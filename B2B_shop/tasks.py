from celery import shared_task
from django.db import transaction
from .models import Seller, TransactionLog
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_charge_task(seller_id, amount_str, unique_id):
    """
    Celery task to process a charge asynchronously.
    This handles the database logic, ensuring the API can return quickly.
    """
    amount = Decimal(amount_str)
    try:
        with transaction.atomic():
            seller = Seller.objects.select_for_update().get(pk=seller_id)

            if seller.credit < amount:
                logger.warning("Charge failed [%s]: insufficient credit (%s)", unique_id, amount)
                return

            # get or Create log and update seller credit
            log, created = TransactionLog.objects.create(
                unique_id=unique_id,
                seller=seller,
                transaction_type='charge_sale',
                amount=-amount,
                balance_after=new_balance
            )

            if not created:
                logger.info("Charge [%s] already processed—skipping.", unique_id)
                return

            new_balance = seller.credit - amount
            


            seller.credit = new_balance
            seller.save()
            print(f"Charge successful for {unique_id}.")
            
    except Seller.DoesNotExist:
        print(f"Charge failed for {unique_id}: Seller not found.")
    except Exception as e:
        # The transaction will roll back automatically on error.
        print(f"An unexpected error occurred during charge {unique_id}: {e}")