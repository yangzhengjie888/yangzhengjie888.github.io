from scholarly import scholarly
import json
import logging
from datetime import datetime
import os


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    logger = logging.getLogger('citation_crawler')
    scholar_id = os.environ.get('GOOGLE_SCHOLAR_ID', '').strip()
    if not scholar_id:
        raise ValueError('GOOGLE_SCHOLAR_ID is missing or empty.')

    scholarly.set_logger(True)
    scholarly.set_timeout(15)
    scholarly.set_retries(2)
    # scholarly 1.5.1 can retry HTTP 403/CAPTCHA indefinitely even with
    # set_retries configured. Keep the workflow's outer timeout as well.
    logger.info('Fetching Google Scholar author profile...')
    author: dict = scholarly.search_author_id(scholar_id)
    logger.info('Profile fetched; fetching citation statistics and publications...')
    scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
    if not isinstance(author.get('citedby'), int) or author['citedby'] < 0:
        raise ValueError('Profile did not contain a valid citation count; no data written.')

    author['updated'] = str(datetime.now())
    author['publications'] = {v['author_pub_id']: v for v in author['publications']}
    shieldio_data = {
        'schemaVersion': 1,
        'label': 'citations',
        'message': str(author['citedby']),
    }
    os.makedirs('results', exist_ok=True)
    with open('results/gs_data.json', 'w', encoding='utf-8') as outfile:
        json.dump(author, outfile, ensure_ascii=False)
    with open('results/gs_data_shieldsio.json', 'w', encoding='utf-8') as outfile:
        json.dump(shieldio_data, outfile, ensure_ascii=False)
    logger.info(
        'Saved citation data: %d citations, %d publications.',
        author['citedby'], len(author['publications']),
    )


if __name__ == '__main__':
    main()
