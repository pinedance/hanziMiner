# -*- encoding:utf8 -*-

from collections import defaultdict, namedtuple, Counter
from itertools import chain, combinations
from hanziminer import Tools, Corpus
import sys
import re
import math

class COQuantifier:  # co-occurrence

    score_header = ['total_freq', 'observed_cooccurrence', 'expected_cooccurrence', 't_score', 'sLLRatio']

    def __init__( self ):
        """"""

    def load( self, text_segmented, doc_sep="(\r?\n){2,}", token_sep="[\s]+"  ):
        self.text = text_segmented
        self.doc_sep = doc_sep
        self.docs = list( map( lambda x: x.strip(), re.split( re.compile( self.doc_sep ), self.text ) ) )
        self.doc_size = len( self.docs )
        self.token_sep = token_sep
        return self

    def count( self, cutoff=5 ):
        self._count_freq( cutoff )._count_cooccurrence()
        print("# All Tokens were Counted")
        return self

    def _count_freq( self, cutoff=5 ):
        """ 전체 단어 빈도 조사 """
        self.tokens_all = Corpus.tokenize( self.text, self.token_sep )
        self.token_size = len( self.tokens_all )
        self.token_freq_all = Counter( self.tokens_all )
        self.token_freq = Counter({ x : self.token_freq_all[x] for x in self.token_freq_all if self.token_freq_all[x] >= cutoff })
        self.tokens = list( self.token_freq.keys() )
        return self

    def _count_cooccurrence( self, allow_duplicate_counts=True ): #doc 안에 같이 나오면 같이 등장하는 것으로.
        """ 문단 별 공기어 빈도 누적 (한 문단 안에 중복해 나와도 거듭 카운트) """
        _cooccurrence = defaultdict(lambda: 0)
        sys.stdout.flush()
        print("# Co-occurrence Counting ... ")
        for i, doc in enumerate( self.docs ):
            _lines = re.split(r"\r?\n", doc)
            _count = Counter()
            for line in _lines:
                _token_candis_all = Corpus.tokenize( line, self.token_sep )
                _token_candis = [ token for token in _token_candis_all if token in self.tokens]
                _count.update( Counter( _token_candis ) )
            _keys = _count.keys()
            for pair in combinations( _keys, 2 ) :
                _cooccurrence[ pair ] += _count[ pair[1] ]
            Tools.print_progress(i+1, self.doc_size, prefix='Progress', suffix='Complete')
        self.cooccurrence = _cooccurrence
        sys.stdout.flush()
        print("# Co-occurrence Counting was done. System memory {:.3f} Gb used".format( Tools.get_process_memory()) )
        return self

    def score( self ):
        # t-score
        _scores = defaultdict( lambda: 0)
        # template
        _tpl = namedtuple("Scores", self.score_header ) # ['total_freq', 'observed_cooccurrence', 'expected_cooccurrence', 't_score']
        total_len = len( self.cooccurrence )
        print("# Co-occurrence Scores Generating ... ")
        i = 0
        for a, b in self.cooccurrence:
            _freq_a, _freq_b = self.token_freq[a], self.token_freq[b]
            _observed = self.cooccurrence[ (a,b) ]
            _expected = ( _freq_a * _freq_b ) / self.token_size
            _t_score = self.__class__.get_Tscore( _observed, _expected )
            _sllr = self.__class__.get_SimpleLogLikelihoodRatio( _observed, _expected )
            _scores[ (a,b) ] = _tpl( ( _freq_a, _freq_b ),  _observed, _expected,  _t_score, _sllr )
            Tools.print_progress(i+1, total_len, prefix='Progress', suffix='Complete')
            i += 1
        self._scores = _scores
        sys.stdout.flush()
        print("# Co-occurrence Scores were generated. System memory {:.3f} Gb used".format( Tools.get_process_memory() ) )
        return self

    def export( self, file_name, target_token, method="t_score", cutoff=1.5  ):
        stream = open(file_name, 'w', encoding="utf-8")
        stream.write( "\t".join( [ "tokens" ] + self.score_header ) + "\n" )
        _rst = self.report( target_token, method, cutoff )
        for token, score in _rst:
            _tmp = list( score )
            _freq = [ str( _tmp[0][1] ), str( _tmp[1] ) ]
            _etc = list( map( lambda x: "{:.3f}".format(x), _tmp[2:] ) )
            stream.write( "\t".join(  [ token ] + _freq + _etc )  + "\n" )
        print("# Report File was exported ")


    def report( self, target_token, method="t_score", cutoff=1.5 ):
        _rst = [ ( b, self._scores[(a,b)] ) for (a, b) in self._scores if a == target_token ]
        _rst_gt = [ (b, sc) for b, sc in _rst if getattr(sc, method) >= cutoff ]
        return sorted( _rst_gt, key=lambda x: getattr(x[1], method), reverse=True )

    @staticmethod
    def get_Tscore( observed , expected ):
        if observed == 0:
            return 0
        else:
            return float( observed - expected ) / math.sqrt( observed )

    def get_SimpleLogLikelihoodRatio( observed , expected  ):
        _rst = 2 * ( ( observed * math.log( ( observed / expected ), 2) ) - ( observed - expected ) )
        rst = _rst if observed >= expected else -1 * _rst
        return rst



class COQuantifierDocs(COQuantifier):
    def __init__(self):
        pass

class COQuantifierPairs(COQuantifier):
    def __init__(self):
        pass

class COQuantifierWindow(COQuantifier):
    def __init__(self, half_window=10):
        self.half_window = half_window

    def load( self, text_unsegmented, doc_sep="(\r?\n){2,}" ):
        self.text = text_unsegmented
        self.doc_sep = doc_sep
        self.line_end = line_end
        return self

    def subtext( self, target_token ):
        self.target_token = target_token
        win_size = ( self.half_window * 2 )
        segs = re.split( re.compile(target_token), self.text )
        segs_size = len(segs)
        subtxt = []
        for i, seg in enumerate( segs ):
            if i == 0:
                if len(seg) < self.half_window: subtxt.append( seg )
                else: subtxt.append( seg[(-1 * self.half_window):] )
                continue
            if i == ( segs_size - 1 ):
                if len(seg) < self.half_window: subtxt.append( seg )
                else: subtxt.append( seg[:self.half_window] )
                continue
            if len(seg) <= win_size: subtxt.append( seg )
            else: subtxt.append( seg[:self.half_window] ); subtxt.append( seg[(-1 * self.half_window):] )

        self._subtext = [ txt for txt in subtxt if len(txt) > 0 ]

    def score( self, segmenter=SegmenterGram(), keyword_only=False ):
        subtext_count = Counter( segmenter.load( " ".join( self._subtext ) ).segment().to_list(keyword_only=keyword_only) )
        _scores = defaultdict( lambda: 0)
        # template
        _tpl = namedtuple("Scores", self.score_header ) # ['total_freq', 'observed_cooccurrence', 'expected_cooccurrence', 't_score']

        print("# Co-occurrence Scores Generating ... ")
        i = 0
        for tk, fq in subtext_count.items():
            _freq_a, _freq_b = self.text.count( self.target_token ), self.text.count( tk )
            _observed = fq
            _expected = ( _freq_a * _freq_b ) len() / len( self.text )
            _t_score = self.__class__.get_Tscore( _observed, _expected )
            _sllr = self.__class__.get_SimpleLogLikelihoodRatio( _observed, _expected )
            _scores[ (a,b) ] = _tpl( ( _freq_a, _freq_b ),  _observed, _expected,  _t_score, _sllr )
            Tools.print_progress(i+1, total_len, prefix='Progress', suffix='Complete')
            i += 1
        sys.stdout.flush()
        print("# Co-occurrence Scores were generated. System memory {:.3f} Gb used".format( Tools.get_process_memory() ) )
        self._scores[self.target_token] = _scores
        return self
