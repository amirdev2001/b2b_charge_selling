import asyncio
import uuid
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.test import TestCase
from django.db import transaction
from django.db.models import F, Sum
from .models import Seller, TransactionLog


class AccountingIntegrityTest(TestCase):
    """
    Test case with 2 sellers, 10 credit additions, and 1000 concurrent sales.
    It verifies the final credit of sellers and the integrity of the transaction logs.
    """

    @sync_to_async
    def get_transaction_sum(self, seller):
        result = TransactionLog.objects.filter(seller=seller).aggregate(total=Sum('amount'))
        return result['total'] or Decimal('0.00')
    
    async def test_concurrent_charging_and_accounting(self):
        # 1. SETUP: Create 2 sellers
        user1 = await User.objects.acreate(username="user1", password="password1")
        user2 = await User.objects.acreate(username="user2", password="password2")

        seller1 = await Seller.objects.acreate(user=user1, name="Seller One")
        seller2 = await Seller.objects.acreate(user=user2, name="Seller Two")

        # 2. CREDIT ADDITIONS (sync wrapped)
        initial_credit1, initial_credit2 = await self.credit_sellers(seller1.id, seller2.id)

        # 3. CONCURRENT SALES: 1000 total (500 per seller)
        charge_amount = Decimal('50.00')
        num_charges_per_seller = 500

        expected_balance1 = initial_credit1 - (num_charges_per_seller * charge_amount)
        expected_balance2 = initial_credit2 - (num_charges_per_seller * charge_amount)

        tasks = []
        for _ in range(num_charges_per_seller):
            tasks.append(self.simulate_charge(seller1.id, charge_amount))
            tasks.append(self.simulate_charge(seller2.id, charge_amount))

        await asyncio.gather(*tasks)

        # 4. VERIFICATION
        final_seller1 = await Seller.objects.aget(pk=seller1.id)
        final_seller2 = await Seller.objects.aget(pk=seller2.id)

        print(f"Seller 1 Final Expected: {expected_balance1}, Actual: {final_seller1.credit}")
        print(f"Seller 2 Final Expected: {expected_balance2}, Actual: {final_seller2.credit}")
        self.assertEqual(final_seller1.credit, expected_balance1)
        self.assertEqual(final_seller2.credit, expected_balance2)

        log_sum1 = await self.get_transaction_sum(final_seller1)
        log_sum2 = await self.get_transaction_sum(final_seller2)

        print(f"Seller 1 Log Sum: {log_sum1}")
        print(f"Seller 2 Log Sum: {log_sum2}")
        self.assertEqual(log_sum1, expected_balance1)
        self.assertEqual(log_sum2, expected_balance2)

    @sync_to_async
    def credit_sellers(self, seller1_id, seller2_id):
        seller1 = Seller.objects.get(id=seller1_id)
        seller2 = Seller.objects.get(id=seller2_id)

        initial_credit1 = Decimal('0.00')
        initial_credit2 = Decimal('0.00')

        with transaction.atomic():
            for _ in range(10):
                credit_amount1 = Decimal('10000.00')
                seller1.credit += credit_amount1
                initial_credit1 += credit_amount1
                TransactionLog.objects.create(
                    seller=seller1,
                    transaction_type='add_credit',
                    amount=credit_amount1,
                    balance_after=seller1.credit
                )

                credit_amount2 = Decimal('15000.00')
                seller2.credit += credit_amount2
                initial_credit2 += credit_amount2
                TransactionLog.objects.create(
                    seller=seller2,
                    transaction_type='add_credit',
                    amount=credit_amount2,
                    balance_after=seller2.credit
                )

            seller1.save()
            seller2.save()

        return initial_credit1, initial_credit2

    @sync_to_async
    def simulate_charge(self, seller_id, amount):
        try:
            with transaction.atomic():
                seller = Seller.objects.select_for_update().get(pk=seller_id)
                if seller.credit >= amount:
                    new_balance = seller.credit - amount
                    TransactionLog.objects.create(
                        unique_id=uuid.uuid4(),
                        seller=seller,
                        transaction_type='charge_sale',
                        amount=-amount,
                        balance_after=new_balance
                    )
                    seller.credit = new_balance
                    seller.save()
        except Exception as e:
            print(f"Simulated charge failed: {e}")
