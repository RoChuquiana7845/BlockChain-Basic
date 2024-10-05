from django.db import models

# Create your models here.
class Block (models.Model): 
    index = models.IntegerField()
    previous_hash = models.CharField(max_length=64)
    timestamp = models.DateTimeField()
    data_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64)
    validator = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        verbose_name = "Block"
        verbose_name_plural = "Blocks"
        ordering = ('index',)

    def __str__(self):
        return f"Block {self.index} - Hash: {self.hash}"


class Transaction(models.Model):
    type = models.CharField(max_length=255)
    data = models.TextField()
    hash = models.CharField(max_length=64)
    block = models.ForeignKey(Block, related_name='transactions', on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ('block',)

    def __str__(self):
        return f"Transaction {self.type} - Hash: {self.hash}"