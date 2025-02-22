# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from argparse import Namespace, ArgumentParser
from simuleval.data.segments import Segment, TextSegment, SpeechSegment, EmptySegment
from .states import AgentStates
from .actions import Action


SEGMENT_TYPE_DICT = {"text": TextSegment, "speech": SpeechSegment}


class GenericAgent:
    """
    Generic Agent class.
    """

    source_type = None
    target_type = None

    def __init__(self, args: Namespace) -> None:
        self.args = args
        assert self.source_type
        assert self.target_type

        self.states = self.build_states()
        self.reset()

    def build_states(self) -> AgentStates:
        """
        Build states instance for agent

        Returns:
            AgentStates: agent states
        """
        return AgentStates()

    def reset(self) -> None:
        """
        Reset agent, called every time when a new sentence coming in.
        """
        self.states.reset()

    def policy(self) -> Action:
        """
        The policy to make decision every time
        when the system has new input.
        The function has to return an Action instance

        Returns:
            Action: The actions to make at certain point.

        .. note:

            WriteAction means that the system has a prediction.
            ReadAction means that the system needs more source.
        """
        assert NotImplementedError

    def push(self, source_segment: Segment) -> None:
        """
        The function to process the incoming information.

        Args:
            source_info (dict): incoming information dictionary
        """
        self.states.update_source(source_segment)

    def pop(self) -> Segment:
        """
        The function to generate system output.
        By default, it first runs policy,
        and than returns the output segment.
        If the policy decide to read,
        it will return an empty segment.


        Returns:
            Segment: segment to return.
        """

        if self.states.target_finished:
            return EmptySegment(finished=True)

        action = self.policy()
        if not isinstance(action, Action):
            raise RuntimeError(
                f"The return value of {self.policy.__qualname__} is not a {Action.__qualname__} instance"
            )
        if action.is_read():
            return EmptySegment()
        else:
            if isinstance(action.content, Segment):
                return action.content

            segment = SEGMENT_TYPE_DICT[self.target_type](
                index=0, content=action.content, finished=action.finished
            )
            self.states.update_target(segment)
            return segment

    def pushpop(self, segment: Segment) -> Segment:
        """
        Operate pop immediately after push.

        Args:
            segment (Segment): input segment

        Returns:
            Segment: output segment
        """
        self.push(segment)
        return self.pop()

    @staticmethod
    def add_args(parser: ArgumentParser):
        """
        Add agent arguments to parser.
        Has to be a static method.

        Args:
            parser (ArgumentParser): cli argument parser
        """
        pass

    @classmethod
    def from_args(cls, args):
        return cls(args)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}[{self.source_type} -> {self.target_type}]"

    def __str__(self) -> str:
        return self.__repr__()


class SpeechToTextAgent(GenericAgent):
    """
    Same as generic agent, but with explicit types
    speech -> text
    """

    source_type: str = "speech"
    target_type: str = "text"


class SpeechToSpeechAgent(GenericAgent):
    """
    Same as generic agent, but with explicit types
    speech -> speech
    """

    source_type: str = "speech"
    target_type: str = "speech"


class TextToSpeechAgent(GenericAgent):
    """
    Same as generic agent, but with explicit types
    text -> speech
    """

    source_type: str = "text"
    target_type: str = "speech"


class TextToTextAgent(GenericAgent):
    """
    Same as generic agent, but with explicit types
    text -> text
    """

    source_type: str = "text"
    target_type: str = "text"
