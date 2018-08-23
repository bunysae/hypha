from django.urls import reverse

from opentech.apply.funds.tests.factories.models import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import StaffFactory, UserFactory
from opentech.apply.utils.testing.tests import BaseViewTestCase

from .factories import ReviewFactory, ReviewFormFieldsFactory


class StaffReviewsTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'pk': instance.id, 'submission_pk': instance.submission.id}

    def test_can_access_review(self):
        review = ReviewFactory(author=self.user)
        response = self.get_page(review)
        self.assertContains(response, review.submission.title)
        self.assertContains(response, self.user.full_name)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': review.submission.id}))

    def test_cant_access_other_review(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(submission=submission)
        response = self.get_page(review)
        self.assertEqual(response.status_code, 403)


class StaffReviewListingTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_can_access_review_listing(self):
        submission = ApplicationSubmissionFactory()
        reviews = ReviewFactory.create_batch(3, submission=submission)
        response = self.get_page(submission, 'list')
        self.assertContains(response, submission.title)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))
        for review in reviews:
            self.assertContains(response, review.author.full_name)


class StaffReviewFormTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = ApplicationSubmissionFactory(status='internal_review')

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_can_access_form(self):
        response = self.get_page(self.submission, 'form')
        self.assertContains(response, self.submission.title)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': self.submission.id}))

    def test_cant_access_wrong_status(self):
        submission = ApplicationSubmissionFactory(rejected=True)
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)

    def test_cant_resubmit_review(self):
        ReviewFactory(submission=self.submission, author=self.user)
        response = self.post_page(self.submission, {'data': 'value'}, 'form')
        self.assertEqual(response.context['has_submitted_review'], True)
        self.assertEqual(response.context['title'], 'Update Review draft')

    def test_can_edit_draft_review(self):
        ReviewFactory(submission=self.submission, author=self.user, is_draft=True)
        response = self.post_page(self.submission, {'data': 'value'}, 'form')
        self.assertEqual(response.context['has_submitted_review'], False)
        self.assertEqual(response.context['title'], 'Update Review draft')

    def test_revision_captured_on_review(self):
        field_ids = [f.id for f in self.submission.round.review_forms.first().fields]

        data = ReviewFormFieldsFactory.form_response(field_ids)

        self.post_page(self.submission, data, 'form')
        review = self.submission.reviews.first()
        self.assertEqual(review.revision, self.submission.live_revision)

    def test_can_submit_draft_review(self):
        field_ids = [f.id for f in self.submission.round.review_forms.first().fields]

        data = ReviewFormFieldsFactory.form_response(field_ids)
        data['save_draft'] = True
        self.post_page(self.submission, data, 'form')
        review = self.submission.reviews.first()
        self.assertTrue(review.is_draft)
        self.assertIsNone(review.revision)


class UserReviewFormTestCase(BaseViewTestCase):
    user_factory = UserFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_cant_access_form(self):
        submission = ApplicationSubmissionFactory(status='internal_review')
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)


class ReviewDetailTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'pk': instance.id, 'submission_pk': instance.submission.id}

    def test_review_detail_recommendation(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2)
        review = ReviewFactory(submission=submission, author=self.user, recommendation_yes=True)
        response = self.get_page(review)
        self.assertContains(response, submission.title)
        self.assertContains(response, "<p>Yes</p>")
