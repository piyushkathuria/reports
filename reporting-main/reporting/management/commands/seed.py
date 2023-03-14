from django.core.management.base import BaseCommand
from faker import Faker
from itertools import groupby
import datetime
from progress.bar import Bar
from random import choice, randrange, sample, uniform
from reporting.models import *
import pytz


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.fake = Faker()
        self.customers = [Customer(name=self.fake.company(), email=self.fake.email(), address=self.fake.address(), phone=self.fake.phone_number()) for _ in range(3)]
        for customer in self.customers:
            customer.save()
        self.businesses = [Business(name=self.fake.company()) for _ in range(3)]
        for business in self.businesses:
            business.save()
        bar = Bar('Seeding', max=100)
        for _ in range(100):
            self.seed_job()
            bar.next()
        bar.finish()
        self.stdout.write('Done.')


    def seed_job(self):
        customer = choice(self.customers)
        business = choice(self.businesses)
        job = Job(customer=customer, business=business, name=self.fake.bs()) # Business Soundings phrases
        job.save()
        invoice = self.seed_invoice(business, job)
        items_to_be_paid = sample(list(invoice.line_items.all()), int(len(invoice.line_items.all()) / 2))
        self.pay_line_items(customer, business, items_to_be_paid)


    def seed_invoice(self, business, job):
        invoice = Invoice(
            business=business,
            number=self.fake.numerify(text='!!###'),
            due_date=pytz.utc.localize(
                self.fake.date_time_this_year()),
            status=choice([Invoice.DRAFT, Invoice.PAID, Invoice.UNPAID]),
        )
        invoice.save()
        job_line_item = LineItem(
        job=job,
        description=self.fake.bs(),
        amount=uniform(0, 1000)
        )
        job_line_item.save()
        invoice_line_item = LineItem(
        invoice=invoice,
        job=job,
        description=job_line_item.description,
        amount=job_line_item.amount
        )
        invoice_line_item.save()
        return invoice
    

    def pay_line_items(self, customer, business, items_to_be_paid):
        payment_type = choice(
            [Payment.CHECK, Payment.DEBIT_CARD, Payment.CREDIT_CARD])
        amount = sum([x.amount for x in items_to_be_paid])
        initiated_date = pytz.utc.localize(
            self.fake.date_time_this_year())
        completed_date = initiated_date + datetime.timedelta(days=7)
        payment = Payment(payer=business,  # payer should be a Business instance
                          payee=business,
                          amount=amount,
                          reference=self.fake.numerify(text='!!###'),
                          payment_type=payment_type,
                          initiated_at=initiated_date,
                          completed_at=completed_date,
                          )
        payment.save()
        for invoice_line_item in items_to_be_paid:
            line_item = LineItem(
                payment=payment,
                self_item=invoice_line_item,
                description=invoice_line_item.description,
                amount=invoice_line_item.amount,
            )
            line_item.save()
