from dataclasses import dataclass

from slack_sdk.models.blocks import SectionBlock

from clients.slack.schema import SlackMessageSchema
from utils.log import get_logger

logger = get_logger(__name__)


@dataclass
class Alert:
    id: str
    elementary_database_and_schema: str

    _LONGEST_MARKDOWN_SUFFIX_LEN = 3
    _CONTINUATION_SYMBOL = '...'

    def to_slack(self, is_slack_workflow: bool = False) -> SlackMessageSchema:
        raise NotImplementedError

    @classmethod
    def _format_section_msg(cls, section_msg):
        if len(section_msg) < SectionBlock.text_max_length:
            return section_msg
        return section_msg[
               :SectionBlock.text_max_length - len(cls._CONTINUATION_SYMBOL) - cls._LONGEST_MARKDOWN_SUFFIX_LEN] + \
               cls._CONTINUATION_SYMBOL + section_msg[-cls._LONGEST_MARKDOWN_SUFFIX_LEN:]

    @classmethod
    def _add_fields_section_to_slack_msg(cls, slack_message: dict, section_msgs: list, divider: bool = False):
        fields = []
        for section_msg in section_msgs:
            fields.append({
                "type": "mrkdwn",
                "text": cls._format_section_msg(section_msg)
            })

        block = []
        if divider:
            block.append({"type": "divider"})
        block.append({"type": "section", "fields": fields})
        slack_message['attachments'][0]['blocks'].extend(block)

    @classmethod
    def _add_text_section_to_slack_msg(cls, slack_message: dict, section_msg: str, divider: bool = False):
        block = []
        if divider:
            block.append({"type": "divider"})
        block.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": cls._format_section_msg(section_msg)
            }
        })
        slack_message['attachments'][0]['blocks'].extend(block)
