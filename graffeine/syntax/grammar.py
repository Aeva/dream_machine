
from .validator import *


GRAMMAR = MatchRule(
    ListRule(Exactly("struct"), WordRule("struct name"), SPLAT = ListRule(WordRule("type"), WordRule("name"))),
    ListRule(Exactly("interface"), WordRule("interface name"), SPLAT = ListRule(WordRule("type"), WordRule("name"))),
    ListRule(Exactly("sampler"), WordRule("sampler name"), SPLAT = MatchRule(
        ListRule(Exactly("min_filter"), WordRule("opengl filter enum")),
        ListRule(Exactly("mag_filter"), WordRule("opengl filter enum")))),
    ListRule(Exactly("texture2d"), WordRule("texture name"), SPLAT = MatchRule(
        ListRule(Exactly("format"), WordRule("format enum")),
        ListRule(Exactly("use"), WordRule("sampler name")))),
    ListRule(Exactly("handle"), WordRule("handle name"), WordRule("interface name")),
    ListRule(Exactly("pipeline"), WordRule("draw name"), SPLAT = MatchRule(
        ListRule(Exactly("vs"), StringRule("shader path")),
        ListRule(Exactly("fs"), StringRule("shader path")),
        ListRule(Exactly("use"), WordRule("struct or interface or texture name")),
        ListRule(Exactly("enable"), WordRule("opengl capability enum")),
        ListRule(Exactly("disable"), WordRule("opengl capability enum")),
        ListRule(Exactly("copy"), WordRule("draw name")))),
    ListRule(Exactly("preload"), WordRule("handle name"), StringRule("file path")),
    ListRule(Exactly("renderer"), WordRule("renderer name"), SPLAT = MatchRule(
        ListRule(Exactly("update"), WordRule("handle name")),
        ListRule(Exactly("draw"), WordRule("draw name"), SPLAT = MatchRule(
            ListRule(Exactly("bind"), WordRule("handle name")))))))
