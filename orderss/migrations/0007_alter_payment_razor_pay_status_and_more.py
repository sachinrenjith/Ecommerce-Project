# Generated by Django 4.2.1 on 2023-07-24 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orderss', '0006_alter_order_is_ordered'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='razor_pay_status',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='razorpay_order_id',
            field=models.CharField(max_length=100, null=True),
        ),
    ]