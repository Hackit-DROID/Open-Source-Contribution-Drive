import logging

from django.db import models
from django.utils.text import slugify

logger = logging.getLogger(__name__)


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    description = models.TextField(blank=True)

    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)

    ai_summary = models.TextField(blank=True, help_text="Auto-generated short summary (Gemini).")
    ai_tags = models.CharField(max_length=400, blank=True, help_text="Comma-separated AI-generated tags.")

    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def is_available(self):
        return self.available_copies > 0

    @property
    def tag_list(self):
        return [t.strip() for t in self.ai_tags.split(',') if t.strip()]

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if self.description and (not self.ai_summary or not self.ai_tags):
            try:
                from ai.services import summarize_book, generate_tags

                updated = False
                if not self.ai_summary:
                    summary = summarize_book(self.description)
                    if summary:
                        self.ai_summary = summary
                        updated = True
                if not self.ai_tags:
                    tags = generate_tags(self.title, self.description)
                    if tags:
                        self.ai_tags = ', '.join(tags)
                        updated = True
                if updated:
                    super().save(update_fields=['ai_summary', 'ai_tags'])
            except Exception as exc:
                logger.warning("Gemini AI enrichment failed for book %s: %s", self.pk, exc)
