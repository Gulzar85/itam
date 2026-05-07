from django.db import models, transaction
from django.core.validators import RegexValidator


class SequenceCounter(models.Model):
    """Atomic counter for generating sequential IDs"""
    key = models.CharField(max_length=50, unique=True, primary_key=True)
    year = models.IntegerField()
    value = models.IntegerField(default=0)

    class Meta:
        db_table = 'sequence_counters'

    @classmethod
    def get_next_value(cls, prefix, year=None):
        """Atomically increment and return the next value for given prefix and year"""
        if year is None:
            from django.utils import timezone
            year = timezone.now().year

        key = f"{prefix}-{year}"

        with transaction.atomic():
            counter, created = cls.objects.select_for_update().get_or_create(
                key=key,
                defaults={'year': year, 'value': 0}
            )
            # Reset counter if year changed
            if counter.year != year:
                counter.year = year
                counter.value = 0
                counter.save()

            counter.value += 1
            counter.save()
            return counter.value


class BusinessInfo(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo = models.ImageField(
        upload_to='business_logos/%Y/%m/',
        blank=True,
        null=True,
        help_text="Max size 2MB"
    )
    description = models.TextField()
    address = models.TextField()
    contact_email = models.EmailField(unique=True)
    contact_phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')]
    )
    website = models.URLField(blank=True)

    primary_color = models.CharField(max_length=7, default='#DA291C')
    secondary_color = models.CharField(max_length=7, default='#FFC72C')
    accent_color = models.CharField(max_length=7, default='#FFBD0A')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Business Info"
        verbose_name_plural = "Business Info"
        ordering = ['name']

    def __str__(self):
        return self.name


# models.py
class SocialMediaLink(models.Model):
    PLATFORM_CHOICES = [
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
        ('whatsapp', 'WhatsApp'),
        ('tiktok', 'TikTok'),
        ('github', 'GitHub'),
        ('pinterest', 'Pinterest'),
        ('snapchat', 'Snapchat'),
        ('telegram', 'Telegram'),
        ('discord', 'Discord'),
        ('reddit', 'Reddit'),
        ('medium', 'Medium'),
        ('twitch', 'Twitch'),
    ]

    ICON_MAP = {
        'facebook': 'fab fa-facebook',
        'instagram': 'fab fa-instagram',
        'twitter': 'fab fa-twitter',
        'linkedin': 'fab fa-linkedin',
        'youtube': 'fab fa-youtube',
        'whatsapp': 'fab fa-whatsapp',
        'tiktok': 'fab fa-tiktok',
        'github': 'fab fa-github',
        'pinterest': 'fab fa-pinterest',
        'snapchat': 'fab fa-snapchat',
        'telegram': 'fab fa-telegram',
        'discord': 'fab fa-discord',
        'reddit': 'fab fa-reddit',
        'medium': 'fab fa-medium',
        'twitch': 'fab fa-twitch',
    }

    business = models.ForeignKey(
        BusinessInfo,
        on_delete=models.CASCADE,
        related_name='social_links'
    )
    platform = models.CharField(
        max_length=50,
        choices=PLATFORM_CHOICES
    )
    url = models.URLField()

    @property
    def icon_class(self):
        return self.ICON_MAP.get(self.platform, 'fas fa-link')

    def __str__(self):
        return f"{self.platform} - {self.business.name}"
