# -*- encoding:utf8 -*-

from collections import defaultdict, namedtuple, Counter
from hanziminer import Corpus, Tools
import re

class SegmenterScore:

    def __init__( self, token_with_score, method="cohesion", score_cutoff=0):
        self.score_list = [ ( tk, getattr( sc, method ) ) for tk, sc in token_with_score.items() if getattr( sc, method ) >= score_cutoff  ]
        self.score = dict( self.score_list )
        self.tokens = self.score.keys()

    def load( self, text, min_window=2, max_window=8 ):
        self.target_text = text
        _token_candis = set( Corpus.allgram(text, min_window, max_window) )
        token_candis_with_score = [ ( it, self.score[it] ) for it in _token_candis if it in self.tokens ]
        self.token_candis = sorted( token_candis_with_score, key=lambda x: (-x[1], -len(x[0] )  ) )
        return self

    def segment( self, segment_marker="%" ):
        target_text = self.target_text + ""
        self.segment_marker = segment_marker
        for i, candi in enumerate( self.token_candis ):
            marker = "{0}{0}{1}{0}{0}".format( self.segment_marker, i )
            target_text = marker.join( target_text.split( candi[0] ) )

        self.text_segment_marked = target_text
        return self

    def to_string( self, verbose=False, keyword_only=False, sep=" " ):
        target_text = self.text_segment_marked + ""
        if keyword_only:
            self.text_segmented = sep.join( self.to_list(verbose=False, keyword_only=True) )
        else:
            for i, candi in enumerate( self.token_candis ):
                marker = "{0}{0}{1}{0}{0}".format( self.segment_marker, i )
                seg = "【{0}/{1:01.3f}】".format( candi[0], candi[1] ) if verbose else "【{}】".format( candi[0] )
                target_text = target_text.replace(marker, seg )
            self.text_segmented = target_text
        return self.text_segmented

    def to_list( self, verbose=False, keyword_only=False ):
        target_text = self.text_segment_marked + ""

        if keyword_only:
            rg = re.compile( "\{0}\{0}\d+?\{0}\{0}".format( self.segment_marker ) )
            _segment_list = re.findall( rg, target_text )
            segment_list = [ self.token_candis[ int(it[2:-2]) ] for it in _segment_list ] if verbose else [ self.token_candis[ int(it[2:-2]) ][0] for it in _segment_list ]
        else:
            segment_list= re.split(r"[【】]", self.to_string( verbose=False, keyword_only=False ) )
        self.list_segmented = list( filter( None, segment_list ) )
        return self.list_segmented

class SegmenterGram:
    def __init__( self, gram_size=2 ):
        self.gram_size = gram_size

    def load( self, text ):
        self.target_text = text
        return self

    def segment( self, escape="[ \t]+" ):
        _grams = Corpus.ngram( self.target_text, self.gram_size )
        self.list_segmented = [ gram for gram in _grams if not re.search( re.compile( escape ), gram ) ]
        return self

    def to_string( self, sep=" " ):
        return sep.join( self.list_segmented )

    def to_list( self ):
        return self.list_segmented

class SegmenterDict:
    def __init__( self, token_dict ):
        self.token_dict = token_dict

    def load( self, text ):
        self.target_text = text
        return self

    def segment( self, escape="[ \t]+" ):
        _checked = [False for i in range( len(self.target_text) ) ]
        _tpl = namedtuple('Token', ["token", "index", "length"])
        _sub_tokens = [ _tpl(token, self.target_text.find(token), len(token) ) for token in self.token_dict if self.target_text.find(token) >= 0 ]
        _sub_tokens_sorted = sorted(_sub_tokens, key=lambda x: (x.index, -x.length) )  # idx, length
        _token_candis = []
        for _token_candi in _sub_tokens_sorted:
            b, e = _token_candi.index, ( _token_candi.index + _token_candi.length )
            if _checked[b] : continue
            _checked[b:e] = [True] * _token_candi.length
            _token_candis.append( _token_candi.token )
        self.list_segmented = _token_candis
        return self

    def to_string( self, keyword_only=False, sep=" " ):
        if keyword_only:
            return sep.join( self.list_segmented )
        else:
            _tmp = self.target_text + ""
            for token in self.list_segmented:
                _tmp = _tmp.replace( token, "【{}】".format(token) )
            return _tmp

    def to_list( self, keyword_only=False ):
        if keyword_only:
            return self.list_segmented
        else:
            return list( filter( None, re.split(r"[【】]", self.to_string() ) ) )
