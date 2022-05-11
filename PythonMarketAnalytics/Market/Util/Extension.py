class XString(str):
    def _toDictionary(self, rowSplit, colSplit):
        if rowSplit not in self and colSplit not in self:
            return {}
        d = dict(x.split(rowSplit) for x in self.split(colSplit))
        return {k.strip().lower():v.strip() for k,v in d.items()}




