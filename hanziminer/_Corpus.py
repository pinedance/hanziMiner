# -*- encoding:utf8 -*-

import re
import yaml
import pkg_resources
from hanziminer import Tools


class Corpus:

    def __init__( self, text, doc_sep="(\r?\n){2,}" ):
        self._text = text
        self.doc_sep = doc_sep
        self._docs = []

    def remove_comments( self, comments_header="#" ):
        _comments_pattern = "{}.*?$".format( comments_header )
        self.comments_pattern = re.compile( _comments_pattern, re.MULTILINE|re.DOTALL )
        self._text = re.sub( self.comments_pattern, " ", self._text ).strip()
        print("# Comments were removed")
        return self

    def remove_punctuation( self, punctuations="[,\.\!！\?？\:;＇，ㆍ．／：；｀、。·‥…¨〃∼´～˝\%\-\\\(\)\{\}\[\]\<\>（）［］｛｝‘’“”〔〕〈〉《》「」『』【】%\$]" ):
        self.punctuations_pattern = re.compile( punctuations )
        self._text = re.sub( self.punctuations_pattern , " ", self._text ).strip()
        print("# Punctuations were removed")
        return self

    def remove_chrs( self, chr_types=["Korean", "Alphabet", "Numbers"] ):
        if "Korean" in chr_types:
            self._text = re.sub( re.compile("[가-힣]+"), " ", self._text )
        if "Alphabet" in chr_types:
            self._text = re.sub( re.compile("[a-zA-Z]+"), " ", self._text )
        if "Numbers" in chr_types:
            self._text = re.sub( re.compile("[\d]+"), " ", self._text )
        self._text = self._text.strip()
        print("# {} were removed".format( ", ".join( chr_types  ) ) )
        return self

    def merge_spaces( self ):
        self._text = re.sub( re.compile("[ \t]+"), " ", self._text )
        self._text = re.sub( re.compile("^[ \t]+", re.MULTILINE), "", self._text ).strip()
        print("# Spaces were merged")
        return self

    def merge_duplications(self, dict_path='dicts/duplications.dic') :
        _dict_path = pkg_resources.resource_filename( __name__ , dict_path)
        self._text = self.__class__.merge_chrs( self._text, _dict_path )
        print("# Duplicated Characters were merged")
        return self

    def merge_variants(self, dict_path='dicts/variants.dic' ):
        _dict_path = pkg_resources.resource_filename( __name__ , dict_path)
        self._text = self.__class__.merge_chrs( self._text, _dict_path )
        print("# Variants Characters were merged")
        return self

    def _text2docs( self ):
        docs = re.split( re.compile( self.doc_sep ), self._text )
        self._docs = [ doc.strip().split() for doc in docs ]
        return self

    def extract(self, type="string"):  # type = [string, list]
        if self._docs == []:
            self._text2docs()
        if type == "string":
            return self._text
        else:
            return self._docs

    def to_text(self):
        return self.extract(type="string")

    def to_string(self):
        return self.extract(type="string")

    def to_list(self):
        return self.extract(type="list")

    def export(self, output_filename, plain_text=True ):
        stream = open(output_filename, 'w', encoding="utf-8")
        if plain_text:
            stream.write( self.extract(type="string") )
        else:
            yaml.dump( self.extract(type="list"), stream, default_flow_style=False,  allow_unicode=True )
        stream.close()
        print( "# File {} was Created".format( output_filename ) )


    @staticmethod
    def merge_chrs( text, dict_path ):
        dic = open(dict_path, 'r', encoding='utf-8').readlines()
        _text = text + ""
        for pair in dic:
            a, b = re.split( r"[ \t]+", pair )
            _text = _text.replace( a.strip(), b.strip() )
        return _text

    def tokenize( line, sep="[ \t]+" ):
        _tokens = list( map( lambda x: x.strip(), re.split( re.compile( sep ), line ) ) )
        tokens = list( filter( None, _tokens ) )    # remove empty string
        return tokens

    def ngram( text, n=2 ):
        return [ text[i:i+n] for i in range( 0, len(text) - n + 1 )  ]

    def allgram( text, min_window=2, max_window=8 ):
        len_txt = len(text)
        mx_wd = len_txt if ( len_txt < max_window ) else max_window
        rst = []
        for i in range(min_window, mx_wd + 1):
            rst += Corpus.ngram(text, i)
        return rst
