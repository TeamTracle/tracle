from django.db import models
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank, TrigramSimilarity
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone

class VideoManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return super().get_queryset().annotate(
            num_likes=models.Count('likes'),
            num_dislikes=models.Count('dislikes'),
            views_sum=models.F('views') + models.F('bunnyvideo__views'))

    def public(self):
        qs = self.get_queryset()
        qs = qs.filter(visibility='PUBLIC', published=True, channel__user__banned=False, videostrike__isnull=True)
        return qs.filter(bunnyvideo__status='finished')

    def search(self, query):
        qs = self.public()
        sq = SearchQuery(query)
        sv = SearchVector('title', 'description', 'channel__name')
        sr = SearchRank(sv, sq)
        similarity = TrigramSimilarity('title', query) + TrigramSimilarity('description', query) + TrigramSimilarity('channel__name', query)
        return qs.annotate(rank=sr, similarity=similarity).annotate(score=(models.F('rank') + models.F('similarity')) / 2).filter(score__gt=0.1).order_by('-score')

class UserManager(BaseUserManager):

    def create_user(self, email, password=None):
        if not email or not password:
            raise ValueError('Users must have email and password.')

        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.created = timezone.now()
        user.last_login = timezone.now()
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password=None):
        user = self.create_user(email, password=password)
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email, password=password)
        user.is_superuser = True
        user.staff = True
        user.save(using=self._db)
        return user
