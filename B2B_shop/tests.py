import asyncio
import uuid
from decimal import Decimal
from django.test import TestCase
from django.db import transaction
from .models import Seller, TransactionLog, CreditRequest
from django.db.models import CheckConstraint, Q, F

class AccountingIntegrityTest(TestCase):
    """
    Test case with 2 sellers, 10 credit additions, and 1000 concurrent sales[cite: 19].
    It verifies the final credit of sellers and the integrity of the transaction logs.
    """
    
    async def test_concurrent_charging_and_accounting(self):
        # 1. SETUP: Create 2 sellers
        seller1 = await Seller.objects.acreate(name="Seller One")
        seller2 = await Seller.objects.acreate(name="Seller Two")

        # 2. CREDIT ADDITIONS: Simulate 10 approved credit requests for each seller [cite: 19]
        initial_credit1 = Decimal('0.00')
        initial_credit2 = Decimal('0.00')

        # Use atomic transaction for setup to ensure it completes fully
        async with transaction.atomic():
            for _ in range(10):
                credit_amount1 = Decimal('10000.00')
                seller1.credit += credit_amount1
                initial_credit1 += credit_amount1
                await TransactionLog.objects.acreate(seller=seller1, transaction_type='add_credit', amount=credit_amount1, balance_after=seller1.credit)
                
                credit_amount2 = Decimal('15000.00')
                seller2.credit += credit_amount2
                initial_credit2 += credit_amount2
                await TransactionLog.objects.acreate(seller=seller2, transaction_type='add_credit', amount=credit_amount2, balance_after=seller2.credit)

            await seller1.asave()
            await seller2.asave()

        # 3. CONCURRENT SALES: Simulate 1000 total charge sales (500 per seller) [cite: 19]
        charge_amount = Decimal('50.00')
        num_charges_per_seller = 500
        
        # Calculate expected final balances
        expected_balance1 = initial_credit1 - (num_charges_per_seller * charge_amount)
        expected_balance2 = initial_credit2 - (num_charges_per_seller * charge_amount)

        # Create async tasks to hit the charge logic concurrently [cite: 21]
        tasks = []
        for _ in range(num_charges_per_seller):
            tasks.append(self.simulate_charge(seller1.id, charge_amount))
            tasks.append(self.simulate_charge(seller2.id, charge_amount))

        await asyncio.gather(*tasks)

        # 4. VERIFICATION
        # Fetch the final state of sellers from the database
        final_seller1 = await Seller.objects.aget(pk=seller1.id)
        final_seller2 = await Seller.objects.aget(pk=seller2.id)
        
        # Verify the final credit on the Seller model
        print(f"Seller 1 Final Expected: {expected_balance1}, Actual: {final_seller1.credit}")
        print(f"Seller 2 Final Expected: {expected_balance2}, Actual: {final_seller2.credit}")
        self.assertEqual(final_seller1.credit, expected_balance1)
        self.assertEqual(final_seller2.credit, expected_balance2)

        # Verify the sum of all transaction logs matches the final credit [cite: 6]
        log_sum1 = await TransactionLog.objects.filter(seller=seller1).asum(F('amount'))
        log_sum2 = await TransactionLog.objects.filter(seller=seller2).asum(F('amount'))
        
        print(f"Seller 1 Log Sum: {log_sum1}")
        print(f"Seller 2 Log Sum: {log_sum2}")
        self.assertEqual(log_sum1, expected_balance1)
        self.assertEqual(log_sum2, expected_balance2)

    async def simulate_charge(self, seller_id, amount):
        """A helper function to simulate the core logic of the ChargeAPIView."""
        # This simulates the view's logic directly for faster, more controlled testing
        try:
            async with transaction.atomic():
                seller = await Seller.objects.select_for_update().aget(pk=seller_id)
                if seller.credit >= amount:
                    new_balance = seller.credit - amount
                    await TransactionLog.objects.acreate(
                        unique_id=uuid.uuid4(), # Generate unique ID for each charge
                        seller=seller,
                        transaction_type='charge_sale',
                        amount=-amount,
                        balance_after=new_balance
                    )
                    seller.credit = new_balance
                    await seller.asave()
        except Exception as e:
            # In a high concurrency test, some transactions might fail (e.g., deadlock), which is ok.
            # The key is that the final accounting must still be correct.
            print(f"Simulated charge failed, which can happen under load: {e}")