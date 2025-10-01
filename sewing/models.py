from django.db import models


# Create your models here.


class Brand(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='brands/', blank=True, null=True)

    def __str__(self):
        return self.name


class Specification(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SewingCategory(models.Model):
    name = models.CharField(max_length=100)
    norm = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class PackagingCategory(models.Model):
    name = models.CharField(max_length=100)
    norm = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Accessory(models.Model):
    TYPE_CHOICES = [
        ("KG", "Кг"),
        ("SHT", "Шт"),
        ("M", "Метр"),
    ]
    name = models.CharField(max_length=100)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='accessories/', blank=True, null=True)
    comment = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default="Шт",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.name}-{self.brand}"

    @property
    def full_name(self):
        return f'{self.name} - {self.comment} -({self.brand})'


class Article(models.Model):
    name = models.CharField(max_length=100)
    article = models.CharField(max_length=100)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    sewing_category = models.ForeignKey(SewingCategory,
                                        on_delete=models.CASCADE)
    packaging_category = models.ForeignKey(PackagingCategory,
                                           on_delete=models.CASCADE)
    accessories = models.ManyToManyField("Accessory",
                                         through="ArticleAccessory",
                                         related_name="articles")
    image = models.ImageField(upload_to='articles/', blank=True, null=True)

    def __str__(self):
        return f"{self.name}-{self.article}"

    @property
    def full_name(self):
        return f'{self.name} - {self.article}'

    @property
    def brand_name(self):
        return f'{self.brand.name}'


class ArticleAccessory(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE,
                                related_name="accessory_link")
    accessory = models.ForeignKey(Accessory, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)

    def __str__(self):
        return f"{self.article.full_name} -> {self.accessory.name}"


class Order(models.Model):
    specification = models.ForeignKey(Specification, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE,
                                related_name="article_detail")
    quantity = models.PositiveIntegerField(null=True, blank=True)
    comment = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return f"{self.specification}-{self.article}"

    @property
    def full_name(self):
        return f"{self.specification}-{self.article}"


class OrderVariant(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                              related_name="variant_link")
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"
