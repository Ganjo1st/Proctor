# Unified Region Classification Logic

class RegionClassifier:
    def __init__(self):
        self.regions = []  # A list to store defined regions

    def add_region(self, name, boundaries):
        """ Adds a region with defined boundaries."""
        self.regions.append({'name': name, 'boundaries': boundaries})

    def classify(self, point):
        """ Classifies a point based on defined regions."""
        for region in self.regions:
            if self._is_within_boundaries(point, region['boundaries']):
                return region['name']
        return "Unknown Region"

    def _is_within_boundaries(self, point, boundaries):
        """ Checks if a point is within specified boundaries. This will need to be defined based on your specific requirements."""
        # Implement boundary check logic here (e.g., using coordinates)
        pass

# Example usage:
# classifier = RegionClassifier()
# classifier.add_region('Region A', ((10, 10), (20, 20)))
# print(classifier.classify((15, 15)))  # Should output: Region A
