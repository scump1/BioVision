
import datetime
import time
from concurrent.futures import ProcessPoolExecutor

from controller.algorithms.pellet_sizer.pellet_sizer import PelletSizer
from controller.algorithms.bubble_sizer.bubble_sizer import BubbleSizeAnalyzer
from controller.algorithms.algorithm_manager_class.states.state_baseclass import State

class PelletSizerSingleState(State):
    
    def run_logic(self):
        
        # Grabbing the reference PelletsizerWidget
        reference = self.data.get_data(self.data.Keys.PELLET_SIZER_WIDGET_REFERENCE, self.data.Namespaces.DEFAULT)

        ### Get the information
        self.target_paths = self.data.get_data(self.data.Keys.PELLET_SIZER_IMAGES, self.data.Namespaces.DEFAULT)
        self.target_settings = self.data.get_data(self.data.Keys.PELLET_SIZER_IMAGE_SETTINGS, self.data.Namespaces.DEFAULT)
        
        pelletsizer = PelletSizer()

        reference._progressbar_update(0.2)
        
        results = []
        with ProcessPoolExecutor() as executor:
            
            try:
                futures = []
                for i, path in enumerate(self.target_paths):
                    
                    print(f"Target path: {path}, target settings: {self.target_settings[i]}")
                    futures.append(executor.submit(pelletsizer.processing, path, True, self.target_settings[i]))
                
                reference._progressbar_update(0.5)
                
                for future in futures:
                    result = future.result()

                    if results is not None:
                        results.append(result)

                reference._progressbar_update(0.9)

            except Exception as e:
                self.logger.error(f"Error occured in pellet sizer: {e}.")

        self.data.add_data(self.data.Keys.PELLET_SIZER_RESULT, results, self.data.Namespaces.DEFAULT)

        reference.pellet_sizing_done.emit()
        
class BubbleSizerSingleState(State):
    
    def run_logic(self):
        
        ### Get the information
        self.target_path = self.data.get_data(self.data.Keys.SI_FILEPATH_TARGET, self.data.Namespaces.DEFAULT)
        
        self.bubble_size()
        
    def bubble_size(self):
        
        try:
            self.logger.info("Single Image Analysis.")
                        
            self.sizer = BubbleSizeAnalyzer()

            with ProcessPoolExecutor() as excecutor:
                
                future = excecutor.submit(self.sizer.process_image, self.target_path, True)

                result = future.result() 
                
                if result is not None:
                    self.data.add_data(self.data.Keys.SI_RESULT, result, self.data.Namespaces.DEFAULT)
                else:
                    self.logger.warning("Null future return.")   
                           
        except Exception as e:
            self.logger.warning(f"Bubble Sizing Error: {e}.")

class BubbleSizerState(State):
    
    def run_logic(self):
        
        try:
            # This control how much instances run parallel -> max is 10
            self.instance_counter = 0
            
            runcondition = True
            resourcespace = self.data.get_data(self.data.Keys.CURRENT_RESOURCE_SPACE, namespace=self.data.Namespaces.MEASUREMENT)
            
            self.instance.measurement_start_event.wait()
            
            # self.calibpath = self.data.get_data(self.data.Keys.CALIBRATION_IMAGE_PATH, self.data.Namespaces.MEASUREMENT)
            # if not os.path.exists(self.calibpath):
            #     self.logger.error("No calibration image.")
            #     return
            
            self.sizer = BubbleSizeAnalyzer()

            while runcondition and not self.terminated:
                runcondition = datetime.datetime.now() < self.runtime_target or not self.stacked_images != self.processed_images
                
                self.get_resources(resourcespace)
                
                # The algorithms profit from parallelization alot 
                if self.img_stack:
                    if self.instance_counter <= (10 - self.instance_counter):
                        try:
                            self.instance_counter += 1
                            self.batch_size = min(len(self.img_stack), 5)
                            batch = self.img_stack[:self.batch_size]

                            self.bubble_size(batch)
                            
                            # Adding to the processing logic
                            self.processed_images.update(batch)
                            self.img_stack = self.img_stack[self.batch_size:]

                        except Exception as e:
                            self.logger.error(f"Error in executing Bubble Sizer: {e}")                            

                self.logger.info("Running the image analyzer schedule.")
                time.sleep(1)
            
            # Cleanup
            self.res_man.delete_resource_space(resourcespace)
            self.img_stack.clear()
            self.stacked_images.clear()
            self.processed_images.clear()
            
        except Exception as e:
            self.logger.warning(f"Error in resolving Bubble Sizer: {e}.")
            
    def bubble_size(self, paths: list) -> None:

        try:
            self.logger.info("Trying to analyze images.")
     
            with ProcessPoolExecutor() as executor:
                try:# Submit tasks and collect futures
                    futures = {
                        executor.submit(self.sizer.process_image, path): path for path in paths
                    }

                    for future in futures:
                    
                        result = future.result(timeout=5)  # A single images takes about 300ms so 5s blocking call should be PLENTY
                        
                        if result is not None:
                            self.alg_data_writer.bubble_size_writer(result)
                        else:
                            self.logger.warning("Null future return.")
                            
                except Exception as e:
                    self.logger.error(f"Error retrieving result: {e}")
         
        except Exception as e:
            self.logger.error(f"Bubble Sizer - Error in resolving parallelization: {e}.")
        
        finally:
            self.instance_counter -= 1