"""公開原稿・配布画像・既存OCR保存フローの検証。"""
from io import BytesIO, StringIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from PIL import Image
import pypdf

from vocab.models import Word
from wordbank.models import WordList


ROOT = Path(settings.BASE_DIR)


def load_samples():
    return json.loads((ROOT / 'demo/data/samples.json').read_text(encoding='utf-8-sig'))


class DemoSampleMaterialTests(SimpleTestCase):
    def test_public_manuscript_fits_models_and_ocr_does_not_overlap(self):
        samples = load_samples()
        self.assertEqual([len(book['words']) for book in samples['wordlists']], [50, 20])
        for book in samples['wordlists']:
            self.assertLessEqual(len(book['name']), 30)
            numbers = [word['number'] for word in book['words']]
            self.assertEqual(numbers, list(range(1, len(numbers) + 1)))
        ocr = samples['ocr_samples']
        target = next(book for book in samples['wordlists']
                      if book['name'] == ocr['target_wordlist_name'])
        self.assertEqual([word['number'] for word in ocr['words']], list(range(51, 61)))
        self.assertTrue(set(word['number'] for word in target['words']).isdisjoint(
            word['number'] for word in ocr['words']))
        for words in [book['words'] for book in samples['wordlists']] + [ocr['words']]:
            for word in words:
                self.assertIs(type(word['number']), int)
                self.assertGreater(word['number'], 0)
                self.assertTrue(0 < len(word['term']) <= 30)
                self.assertTrue(0 < len(word['meaning']) <= 100)

    def test_cli_generates_readable_size_jpeg_and_committed_image_exists(self):
        font = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
        if not font.exists():
            self.skipTest('画像生成検証にはREADME記載のNoto CJKフォントが必要です。')
        with TemporaryDirectory() as directory:
            output = Path(directory) / 'sample.jpg'
            result = subprocess.run([
                sys.executable, str(ROOT / 'scripts/render_demo_ocr_sample.py'),
                '--font', str(font), '--output', str(output),
            ], capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            for path in (output, ROOT / 'docs/demo-samples/ocr-sample-en.jpg'):
                with Image.open(path) as image:
                    self.assertEqual(image.format, 'JPEG')
                    self.assertGreaterEqual(image.width, 1000)
                    self.assertGreaterEqual(image.height, 1000)
                    self.assertLess(image.convert('L').getextrema()[0], 100)


class DemoSampleOcrTests(TestCase):
    def test_existing_ocr_can_confirm_edit_and_append_all_ten_words(self):
        call_command('initialize_runtime', stdout=StringIO())
        user = get_user_model().objects.get(username=settings.DEMO_USERNAME)
        self.client.force_login(user)
        sample = load_samples()['ocr_samples']
        wordlist = WordList.objects.get(name=sample['target_wordlist_name'])
        self.assertEqual(wordlist.words.count(), 50)
        self.assertEqual(self.client.get(reverse('ocr:interface'),
                                        {'wordlist': wordlist.pk}).status_code, 200)
        content = {word['term']: {'number': word['number'], 'meaning': word['meaning']}
                   for word in sample['words']}
        completion = SimpleNamespace(id='demo-sample-ocr', model='gpt-4o-mini',
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50),
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(content)))])
        # 外部API応答だけを置換する。画像取込・抽出整形・保存は既存処理を使う。
        with override_settings(API_KEY='test-only'), patch(
                'openai.resources.chat.completions.Completions.create', return_value=completion):
            response = self.client.post(reverse('ocr:ocr'), {'files': SimpleUploadedFile(
                'ocr-sample-en.jpg', (ROOT / 'docs/demo-samples/ocr-sample-en.jpg').read_bytes(),
                content_type='image/jpeg')})
        self.assertEqual(response.status_code, 200)
        extracted = response.json()['words']
        self.assertEqual(extracted, sample['words'])
        # 確認画面で訳を修正したときと同じ登録要求を送る。
        extracted[0]['meaning'] = '窓（確認して編集）'
        for word in extracted:
            saved = self.client.post(reverse('vocab:register'), word | {'wordlist': wordlist.pk})
            self.assertEqual(saved.status_code, 201)
        self.assertEqual(wordlist.words.count(), 60)
        self.assertEqual(list(wordlist.words.filter(number__gte=51).order_by('number').values(
            'number', 'term', 'meaning')), extracted)
        self.assertFalse(Word.objects.filter(wordlist=wordlist).exclude(latest_edited_by=user).exists())


class DemoSampleExperienceTests(TestCase):
    def setUp(self):
        call_command('initialize_runtime', stdout=StringIO())
        self.user = get_user_model().objects.get(username=settings.DEMO_USERNAME)
        self.client.force_login(self.user)

    def post_json(self, name, data, client=None):
        return (client or self.client).post(reverse(name), json.dumps(data),
                                            content_type='application/json')

    def test_shared_account_edit_is_visible_in_another_session(self):
        other = Client()
        other.force_login(self.user)
        wordlist = WordList.objects.get(name='デモ英単語50')
        word = wordlist.words.get(number=1)
        self.assertNotEqual(self.client.session.session_key, other.session.session_key)
        self.assertEqual(self.post_json('vocab:update', {
            'id': word.pk, 'number': 1, 'term': word.term, 'meaning': 'りんご（共有編集）',
        }).status_code, 200)
        visible = self.post_json('wordbank:read', {'id': wordlist.pk}, client=other)
        self.assertEqual(visible.json()['words'][0]['meaning'], 'りんご（共有編集）')
        self.assertContains(other.get(reverse('vocab:editor')), 'デモ環境')

    def test_sample_ranges_random_directions_preview_and_real_pdf(self):
        english = WordList.objects.get(name='デモ英単語50')
        configure = {'wordlistId': english.pk, 'numQuestion': 10,
                     'sequence': 'sequence', 'format': 'qfr-tm'}
        for start in (1, 11):
            configure['ranges'] = [{'start': start, 'end': start + 9}]
            self.assertEqual(self.post_json('quiz:preview', configure).status_code, 200)
            preview = self.client.get(reverse('quiz:preview'))
            self.assertEqual([word['number'] for word in preview.context['words']],
                             list(range(start, start + 10)))
        configure.update(ranges=[{'start': 11, 'end': 30}], sequence='random')
        self.assertEqual(self.post_json('quiz:preview', configure).status_code, 200)
        numbers = [word['number'] for word in self.client.get(
            reverse('quiz:preview')).context['words']]
        self.assertEqual(len(numbers), 10)
        self.assertEqual(len(set(numbers)), 10)
        self.assertTrue(all(11 <= number <= 30 for number in numbers))

        with TemporaryDirectory() as directory, override_settings(OUTPUT_PDF_DIR=directory):
            for book in WordList.objects.order_by('pk'):
                for direction in ('qfr-tm', 'qfr-mt'):
                    with self.subTest(book=book.name, direction=direction):
                        config = {'wordlistId': book.pk, 'ranges': [{'start': 1, 'end': 10}],
                                  'numQuestion': 10, 'sequence': 'sequence', 'format': direction}
                        self.assertEqual(self.post_json('quiz:preview', config).status_code, 200)
                        preview = self.client.get(reverse('quiz:preview'))
                        expected = list(book.words.filter(number__lte=10).values(
                            'number', 'term', 'meaning'))
                        if direction == 'qfr-mt':
                            expected = [word | {'term': word['meaning'], 'meaning': word['term']}
                                        for word in expected]
                        self.assertEqual(preview.context['words'], expected)
                        self.assertContains(preview, expected[0]['term'])
                        self.assertContains(preview, expected[0]['meaning'])
                        self.assertNotContains(preview, 'デモ環境')
                        response = self.post_json('quiz:create', config)
                        self.assertEqual(response.status_code, 200)
                        pdf = pypdf.PdfReader(BytesIO(b''.join(response.streaming_content)))
                        self.assertEqual(len(pdf.pages), 2)
                        questions, answers = [page.extract_text() for page in pdf.pages]
                        for word in expected:
                            self.assertIn(word['term'], questions)
                            self.assertIn(word['term'], answers)
                            self.assertIn(word['meaning'], answers)
                        self.assertNotIn(expected[0]['meaning'], questions)
                        self.assertNotIn('デモ環境', questions + answers)
