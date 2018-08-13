class KMCorpus: 

    def __init__(self, corpus_txt, num_doc = -1, num_sent = -1, iter_sent = False, skip_header = 0):
        self.corpus_txt = corpus_txt
        self.num_doc = 0
        self.num_sent = 0
        self.iter_sent = iter_sent
        self.skip_header = skip_header
    
    def __iter__(self):
        try:
                f =  self.corpus_txt
                
                # skip headers
                for _ in range(self.skip_header):
                    next(f)
                    
                # iteration
                num_sent, stop = 0, False
                for doc_idx, doc in enumerate(f):
                    if stop:
                        break

                    # yield doc
                    if not self.iter_sent:
                        yield doc
                        if (self.num_doc > 0) and ((doc_idx + 1) >= self.num_doc):
                            stop = True
                        continue

                    # yield sents
                    for sent in doc.split('  '):
                        if (self.num_sent > 0) and (num_sent >= self.num_sent):
                            stop = True
                            break
                        sent = sent.strip()
                        if sent:
                            yield sent
                            num_sent += 1
            finally:
                f.close()

        except Exception as e:
            print(e)

    def __len__(self):
        if self.num_doc == 0:
            self.num_doc, self.num_sent = self._check_length(-1, -1)
        return self.num_sent if self.iter_sent else self.num_doc