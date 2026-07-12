from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Extends Django's built-in AbstractUser. Django's own 'id' field serves as
    Userid, and 'password' is handled + hashed automatically (satisfies NFR R-5).
    Adds 'role' as required by the class diagram and R-15 (Role-Based Access Control).
    """
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Staff', 'Staff'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Staff')

    def resetPassword(self, new_password):
        self.set_password(new_password)
        self.save()

    # login() / logout() are handled via Django's built-in
    # django.contrib.auth.login() / logout() functions in views.py.

    def __str__(self):
        return f"{self.username} ({self.role})"


class InventoryItem(models.Model):
    itemID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    unit = models.CharField(max_length=50)
    quantity = models.FloatField(default=0)
    minThreshold = models.FloatField()
    expirydate = models.DateField(null=True, blank=True)

    def updateQuantity(self, new_quantity):
        self.quantity = new_quantity
        self.save()

    def checkThreshold(self):
        return self.quantity <= self.minThreshold

    def isexpiringsoon(self, warning_days=3):
        if not self.expirydate:
            return False
        return date.today() <= self.expirydate <= date.today() + timedelta(days=warning_days)

    def __str__(self):
        return self.name


class Vendor(models.Model):
    vendorID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    ContactNumber = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    qualityRating = models.FloatField(default=0)

    def getSupplementitems(self):
        return InventoryItem.objects.filter(orders__vendorId=self).distinct()

    def getOrderHistory(self):
        return self.orders.all().order_by('-orderDate')

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]
    OrderId = models.AutoField(primary_key=True)
    vendorId = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='orders')
    itemId = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='orders')
    quantity = models.FloatField()
    totalCost = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    orderDate = models.DateTimeField(auto_now_add=True)

    def placeOrder(self):
        self.status = 'Pending'
        self.save()

    def confirmDelivery(self):
        self.status = 'Delivered'
        self.itemId.updateQuantity(self.itemId.quantity + self.quantity)
        self.save()

    def calculateTotalcost(self, unit_cost):
        self.totalCost = self.quantity * unit_cost
        self.save()
        return self.totalCost

    def __str__(self):
        return f"Order #{self.pk} - {self.itemId} from {self.vendorId}"


class Alert(models.Model):
    TYPE_CHOICES = [
        ('Lowstock', 'Lowstock'),
        ('Empty', 'Empty'),
        ('Expiry', 'Expiry'),
    ]
    alertId = models.AutoField(primary_key=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    message = models.TextField(blank=True)
    itemId = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='alerts')
    IsRead = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)

    @classmethod
    def generate(cls, item, alert_type, message):
        alert = cls.objects.create(type=alert_type, message=message, itemId=item)
        alert.sendNotifications()
        return alert

    def sendNotifications(self):
        # Placeholder: in-app notification only, for this college project's scope.
        pass

    def MarkasRead(self):
        self.IsRead = True
        self.save()

    def __str__(self):
        return f"{self.type} alert - {self.itemId}"


class Forecast(models.Model):
    forecastid = models.AutoField(primary_key=True)
    generatedAt = models.DateTimeField(auto_now_add=True)
    periodstart = models.DateField()
    periodend = models.DateField()
    forecastData = models.JSONField(default=dict, blank=True)

    def generate(self):
        # Implemented in views.py: analyses StockLog usage history
        # within periodstart/periodend to populate forecastData.
        pass

    def applyOccassionfactor(self, factor):
        adjusted = {k: v * factor for k, v in self.forecastData.items()}
        self.forecastData = adjusted
        self.save()
        return adjusted

    def generateReorderSuggestions(self):
        suggestions = []
        for item_id, predicted_qty in self.forecastData.items():
            try:
                item = InventoryItem.objects.get(pk=item_id)
            except InventoryItem.DoesNotExist:
                continue
            if item.quantity < predicted_qty:
                suggestions.append({
                    'item': item,
                    'quantity_to_order': predicted_qty - item.quantity,
                })
        return suggestions

    def __str__(self):
        return f"Forecast {self.periodstart} to {self.periodend}"


class Report(models.Model):
    TYPE_CHOICES = [
        ('Usage', 'Usage'),
        ('Wastage', 'Wastage'),
    ]
    reportId = models.AutoField(primary_key=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    generatedBy = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reports')
    dateRangeStart = models.DateField()
    dateRangeEnd = models.DateField()

    def generate(self):
        # Implemented in views.py: aggregates StockLog entries
        # within dateRangeStart/dateRangeEnd.
        pass

    def exportPDF(self):
        pass

    def exportcsv(self):
        pass

    def __str__(self):
        return f"{self.type} Report ({self.dateRangeStart} - {self.dateRangeEnd})"


class StockLog(models.Model):
    """
    Supporting table (not present in the class diagram) required by:
    - R-4: logs stock changes with timestamp and user ID
    - R-13/R-14: source data for Usage and Wastage reports
    """
    CHANGE_TYPE_CHOICES = [
        ('Restock', 'Restock'),
        ('Usage', 'Usage'),
        ('Wastage', 'Wastage'),
    ]
    logId = models.AutoField(primary_key=True)
    itemId = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='stock_logs')
    userId = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_logs')
    changeType = models.CharField(max_length=10, choices=CHANGE_TYPE_CHOICES)
    quantityChanged = models.FloatField()
    reason = models.CharField(max_length=255, blank=True)
    changedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.changeType} - {self.itemId} ({self.quantityChanged})"
